"""Calibeur RF-104 temperature and humidity sensor (21-bit PWM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class CalibeursRF104(OOKPWMDecoder):
    """Calibeur RF-104 temperature and humidity sensor (21-bit PWM)."""
    name     = "Calibeur-RF104"
    short_us = 760.0
    long_us  = 2240.0
    reset_us = 3200.0
    n_bits   = 21

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 21:
            return None
        b0 = bits_to_int(bits[0:8])
        b1 = bits_to_int(bits[8:16])
        # Pad last byte to 8 bits
        last = bits[16:21] + [0] * 3
        b2 = bits_to_int(last)

        # Extract channel ID and fractional temperature from b0 bits[0:6]
        # Each source bit feeds a specific result bit (bit-reversal of lower 6 bits)
        raw6 = (
            ((b0 & 0x80) >> 7)        # result bit 0
            | ((b0 & 0x40) >> 5)      # result bit 1
            | ((b0 & 0x20) >> 3)      # result bit 2
            | ((b0 & 0x10) >> 1)      # result bit 3
            | ((b0 & 0x08) << 1)      # result bit 4
            | ((b0 & 0x04) << 3)      # result bit 5
        )
        sensor_id   = raw6 // 10
        temp_frac   = (raw6 % 10) * 0.1

        # Integer temperature from b0[1:0] and b1[7:0] (7 bits, offset -41)
        temp_int_val = (
            ((b0 & 0x02) << 3)
            | ((b0 & 0x01) << 5)
            | ((b1 & 0x80) >> 7)
            | ((b1 & 0x40) >> 5)
            | ((b1 & 0x20) >> 3)
            | ((b1 & 0x10) >> 1)
            | ((b1 & 0x08) << 3)
        )
        temp_c = temp_frac + temp_int_val - 41.0

        # Humidity from b1[1:0] and b2[7:3] (7 bits)
        humidity = (
            ((b1 & 0x02) << 4)
            | ((b1 & 0x01) << 6)
            | ((b2 & 0x80) >> 7)
            | ((b2 & 0x40) >> 5)
            | ((b2 & 0x20) >> 3)
            | ((b2 & 0x10) >> 1)
            | ((b2 & 0x08) << 1)
        )
        if not 0 <= humidity <= 100:
            return None
        if not -40.0 <= temp_c <= 80.0:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": sensor_id,
            "temperature_C": round(temp_c, 1),
            "humidity": humidity,
        })


__all__ = ["CalibeursRF104"]
