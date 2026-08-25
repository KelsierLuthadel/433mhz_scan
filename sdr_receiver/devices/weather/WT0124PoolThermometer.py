"""WT0124 Pool Thermometer."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _xor_bytes(data: bytes | bytearray) -> int:
    result = 0
    for b in data:
        result ^= b
    return result


class WT0124PoolThermometer(OOKPWMDecoder):
    """WT0124 Pool Thermometer."""
    name     = "WT0124-Pool"
    short_us = 680.0
    long_us  = 1_850.0
    reset_us = 30_000.0
    n_bits   = 49

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 48:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 48, 8))

        if b[0] >> 4 != 0x5:
            return None

        # XOR checksum
        if _xor_bytes(b[:4]) != b[4]:
            return None

        # Carry-aware additive sum
        s = b[0] + b[1] + b[2] + b[3]
        s = (s & 0xFF) + (s >> 8)
        s = (s + b[4]) & 0xFF
        if s != b[5]:
            return None

        sensor_rid = (b[0] & 0x0F) << 4 | (b[1] & 0x0F)
        temp_raw   = ((b[1] & 0x0F) << 8) | b[2]
        temp_c     = (temp_raw - 0x990) * 0.1
        channel    = (b[3] >> 4) & 0x3

        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_rid,
            "channel":       channel,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["WT0124PoolThermometer"]
