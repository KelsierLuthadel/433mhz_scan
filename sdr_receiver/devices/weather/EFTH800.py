"""Eurochron EFTH-800 Temperature and Humidity Sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ._helpers import _sign16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EFTH800(OOKPWMDecoder):
    """Eurochron EFTH-800 Temperature and Humidity Sensor."""
    name       = "Eurochron-EFTH800"
    short_us   = 250.0
    long_us    = 500.0
    reset_us   = 5_500.0
    n_bits     = 48
    max_offset = 20    # sync pulse (750 µs) may displace frame start

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 48:
            return None
        # Transmitted with inverted polarity
        b = bytes(bits_to_int(bits[i:i + 8]) ^ 0xFF for i in range(0, 48, 8))

        # Reject all-zero junk frames
        if b[0] == 0 and b[1] == 0 and b[2] == 0 and b[4] == 0:
            return None

        # CRC-8 poly=0x31 residue over all 6 bytes (0 = valid)
        if crc8(b, poly=0x31, init=0x00) != 0:
            return None

        channel     = ((b[0] & 0x70) >> 4) + 1       # 0-indexed → 1–8
        sensor_id   = ((b[0] & 0x0F) << 8) | b[1]
        battery_low = (b[2] >> 7) & 1

        # 10-bit signed temp left-aligned in 16-bit word via b[2][5:0] and b[3][7:4]
        # Sign extension: if b[2][5] (= temp MSB) is 1, int16 bit 15 will be set.
        temp_raw16 = _sign16(((b[2] & 0x3F) << 10) | ((b[3] & 0xF0) << 2))
        temp_c     = (temp_raw16 >> 6) * 0.1

        # Humidity in BCD
        humidity = (b[4] >> 4) * 10 + (b[4] & 0x0F)

        if not 0 <= humidity <= 100:
            return None
        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["EFTH800"]
