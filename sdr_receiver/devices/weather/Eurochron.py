"""Eurochron temperature and humidity sensor (36-bit PPM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Eurochron(OOKPPMDecoder):
    """Eurochron temperature and humidity sensor (36-bit PPM)."""
    name     = "Eurochron-TH"
    short_us = 1016.0
    long_us  = 2024.0
    reset_us = 8200.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 32, 8))
        # Lower nibble of byte 1 must be zero
        if (b[1] & 0x0F) != 0:
            return None
        device_id  = b[0]
        battery_ok = not bool((b[1] >> 7) & 1)
        button     = bool((b[1] >> 4) & 1)
        humidity   = b[2]
        if not 0 <= humidity <= 100:
            return None
        # 12-bit temperature in bits[24:36]
        temp_raw = bits_to_int(bits[24:36])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c = temp_raw / 10.0
        if not -50.0 <= temp_c <= 80.0:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id, "battery_ok": battery_ok, "button": button,
            "temperature_C": round(temp_c, 1), "humidity": humidity,
        })


__all__ = ["Eurochron"]
