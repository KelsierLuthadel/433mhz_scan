"""ThermoPro TP-11 Thermometer."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _reflect8(b: int) -> int:
    """Reverse the 8 bits of a byte."""
    result = 0
    for _ in range(8):
        result = (result << 1) | (b & 1)
        b >>= 1
    return result


def _lfsr_digest8_reflect(data: bytes, gen: int, key: int) -> int:
    """LFSR digest with per-byte bit reflection.

    Equivalent to rtl_433's lfsr_digest8_reflect()  each byte is
    bit-reversed before being fed into the LFSR.  Used by TP11/TP12.
    """
    s = 0
    for byte in data:
        byte = _reflect8(byte)
        for i in range(7, -1, -1):
            if (byte >> i) & 1:
                s ^= key
            if key & 1:
                key = ((key >> 1) ^ gen) & 0xFF
            else:
                key = (key >> 1) & 0xFF
    return s


class ThermoProTP11(OOKPPMDecoder):
    """ThermoPro TP-11 Thermometer.

    OOK PPM, 32 bits.
    Integrity: LFSR-digest8-reflect (gen=0x51, key=0x04).
    Layout: device_id[12] | temp_raw[12] | digest[8]
    temp_C = (temp_raw - 200) * 0.1
    """

    name     = "Thermopro-TP11"
    short_us = 500.0
    long_us  = 1500.0
    reset_us = 4000.0
    n_bits   = 32

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 32:
            return None
        b = bytes(bits_to_int(bits[i * 8:(i + 1) * 8]) for i in range(4))
        # Sanity
        if (b[0] == 0 and b[1] == 0 and b[2] == 0 and b[3] == 0) or \
           (b[0] == 0xFF and b[1] == 0xFF and b[2] == 0xFF and b[3] == 0xFF):
            return None
        if _lfsr_digest8_reflect(b[:3], 0x51, 0x04) != b[3]:
            return None
        device   = (b[0] << 4) | (b[1] >> 4)
        temp_raw = ((b[1] & 0x0F) << 8) | b[2]
        temp_c   = (temp_raw - 200) * 0.1
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["ThermoProTP11"]
