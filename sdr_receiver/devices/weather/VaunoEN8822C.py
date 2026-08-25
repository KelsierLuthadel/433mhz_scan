"""Vauno EN8822C Temperature and Humidity Sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _sign16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _add_nibbles(data: bytes | bytearray, n: int) -> int:
    """Sum of all nibbles in the first n bytes."""
    total = 0
    for i in range(n):
        total += (data[i] >> 4) + (data[i] & 0x0F)
    return total


class VaunoEN8822C(OOKPPMDecoder):
    """Vauno EN8822C Temperature and Humidity Sensor."""
    name     = "Vauno-EN8822C"
    short_us = 2_000.0
    long_us  = 4_000.0
    reset_us = 9_500.0
    n_bits   = 42

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 42:
            return None
        # 5 full bytes + 2 bits (stored at top of b[5])
        b = bytearray(bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8))
        b.append(bits_to_int(bits[40:42]) << 6)   # b[5]: upper 2 bits valid

        # 6-bit checksum: low-nibble(b[4])<<2 | top-2-bits(b[5])
        chk   = ((b[4] & 0x0F) << 2) | (b[5] >> 6)
        total = _add_nibbles(b, 4) + (b[4] >> 4)
        if total == 0:
            return None
        if (total & 0x3F) != chk:
            return None

        device_id   = b[0]
        channel     = ((b[1] & 0x30) >> 4) + 1   # 0-indexed → 1–3
        battery_low = (b[4] & 0x10) >> 4

        # 12-bit signed temp left-aligned; (int16>>4)×0.1 °C
        temp_raw16 = _sign16(((b[1] & 0x0F) << 12) | (b[2] << 4))
        temp_c     = (temp_raw16 >> 4) * 0.1

        humidity = b[3] >> 1   # 7-bit field

        if not 0 <= humidity <= 100:
            return None
        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["VaunoEN8822C"]
