"""RainPoint Soil Temperature and Moisture Sensor  ported from rtl_433 C source.

Note: rainpoint_soil.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPCMDecoder
from .._helpers import _bits_to_bytes, _reverse8, _add_nibbles
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _manchester_decode(bits: list[int]) -> list[int] | None:
    """Decode Manchester pairs: (0,1)->0, (1,0)->1.  Returns None on error."""
    result = []
    for i in range(0, len(bits) - 1, 2):
        a, b = bits[i], bits[i + 1]
        if a == 0 and b == 1:
            result.append(0)
        elif a == 1 and b == 0:
            result.append(1)
        else:
            return None
    return result


class RainPointSoil(OOKPCMDecoder):
    """RainPoint Soil Temperature and Moisture Sensor.

    OOK_PULSE_PCM (chip=500 us), Manchester-encoded payload.
    Preamble: 0xaa 0xa9 in raw chips.
    12 decoded bytes: SYNC(2) ID(2) FLAGS(1) STATUS(2) TEMP(1) HUM(1) UNK(1) CHK(1) FIXED(1).
    Checksum = sum of nibbles over bytes 0-9.
    """

    name     = "RainPoint-Soil"
    chip_us  = 500.0
    reset_us = 1500.0
    n_bits   = 232  # minimum raw chip bits

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Search for preamble 10101010 10101001
        preamble = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1]
        n = len(bits)
        start = -1
        for i in range(n - 15):
            if bits[i:i + 16] == preamble:
                start = i + 14  # keep 1 initial data bit per C code
                break
        if start < 0 or start + 24 * 2 > n:
            return None
        # Manchester decode 12 bytes (24 bytes of chips)
        decoded = _manchester_decode(bits[start:start + 12 * 2 * 8])
        if decoded is None or len(decoded) < 12 * 8:
            return None
        # Invert
        decoded = [1 - x for x in decoded]
        b = _bits_to_bytes(decoded[:12 * 8])
        if len(b) < 12:
            return None
        # Reflect bytes
        b = bytes(_reverse8(x) for x in b)
        # Nibble checksum over bytes 0-9
        chk_calc = _add_nibbles(b[:10]) & 0xFF
        if chk_calc != b[10]:
            return None
        sync    = (b[0] << 8) | b[1]
        id_     = (b[2] << 8) | b[3]
        flags   = b[4]
        temp_c  = float((b[7] if b[7] < 128 else b[7] - 256))
        moisture = b[8]
        chan = {0x9F: 1, 0xB1: 2, 0xB7: 3}.get(flags, 0)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           f"{id_:04x}",
            "channel":      chan,
            "temperature_C": temp_c,
            "moisture":     moisture,
        })


__all__ = ["RainPointSoil"]
