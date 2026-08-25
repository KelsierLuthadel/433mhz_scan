"""Digitech XC-0324 / AmbientWeather FT005TH temperature and humidity."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _reverse8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class DigitechXC0324(OOKPPMDecoder):
    """Digitech XC-0324 / AmbientWeather FT005TH temperature and humidity."""
    name     = "Digitech-XC0324"
    short_us = 520.0
    long_us  = 1000.0
    reset_us = 3000.0
    n_bits   = 48

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 48:
            return None
        # Bytes are transmitted LSB-first; reverse each byte's bits
        b = bytes(_reverse8(bits_to_int(bits[i:i+8])) for i in range(0, 48, 8))
        # Preamble must be 0x5F
        if b[0] != 0x5F:
            return None
        # XOR checksum over all 6 bytes must be 0
        if b[0] ^ b[1] ^ b[2] ^ b[3] ^ b[4] ^ b[5] != 0:
            return None
        device_id = b[1]
        # Temperature: 12 bits LSB-first spanning bits[16:28]
        temp_raw = sum(bits[16 + i] << i for i in range(12))
        temp_c   = temp_raw / 10.0 - 40.0
        # Humidity: 8 bits LSB-first at bits[28:36]
        humidity = sum(bits[28 + i] << i for i in range(8))
        if not -40.0 <= temp_c <= 80.0:
            return None
        if not 0 <= humidity <= 100:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id,
            "temperature_C": round(temp_c, 1),
            "humidity": humidity,
        })


__all__ = ["DigitechXC0324"]
