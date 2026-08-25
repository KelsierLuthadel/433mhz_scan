"""Ambient Weather TX-8300 / TFA 30.3211.02 temperature/humidity sensor."""
from __future__ import annotations
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


class AmbientWeatherTX8300(OOKPPMDecoder):
    """Ambient Weather TX-8300 / TFA 30.3211.02 temperature/humidity sensor."""
    name     = "Ambientweather-TX8300"
    short_us = 1_936.0   # short gap → bit 0
    long_us  = 3_888.0   # long  gap → bit 1
    reset_us = 8_000.0
    n_bits   = 74        # 2 preamble + 72 data bits

    @staticmethod
    def _tx8300_chk(data: bytes) -> int:
        """Fletcher-8 style checksum over 8 bytes (4 data + 4 inverted)."""
        s0 = 0
        s1 = 0
        for byte in data:
            s0 = (s0 + byte) & 0xFF
            s1 = (s1 + s0) & 0xFF
        # Combine: high nibble of s1, high nibble of s0
        return ((s1 & 0xF0) | (s0 >> 4)) & 0xFF

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 74:
            return None

        # Skip 2-bit preamble
        data_bits = bits[2:74]
        b = bytes(bits_to_int(data_bits[i:i + 8]) for i in range(0, 72, 8))
        # b[0:4] = data, b[4:8] = inverted, b[8] = checksum

        # Verify byte-wise parity (each data byte XOR'd with its inverse = 0xFF)
        for i in range(4):
            if (b[i] ^ b[i + 4]) != 0xFF:
                return None

        if self._tx8300_chk(b[:8]) != b[8]:
            return None

        # Humidity (BCD)
        hum_tens  = (b[0] >> 4) & 0x0F
        hum_units =  b[0] & 0x0F
        humidity  = hum_tens * 10 + hum_units

        battery_low = bool((b[1] >> 6) & 0x03)
        channel     = ((b[1] >> 4) & 0x03) + 1   # 0-indexed → 1-indexed
        sign        = bool((b[1] >> 3) & 0x01)
        sensor_id   = ((b[1] & 0x07) << 4) | (b[2] >> 4)   # 7 bits

        # Temperature BCD (three digits: hundreds, tens, units)
        temp_h = b[2] & 0x0F
        temp_t = (b[3] >> 4) & 0x0F
        temp_u =  b[3] & 0x0F
        temp_c = temp_h * 10.0 + temp_t + temp_u * 0.1
        if sign:
            temp_c = -temp_c

        if not 0 <= humidity <= 100:
            return None
        if not -40.0 <= temp_c <= 60.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["AmbientWeatherTX8300"]
