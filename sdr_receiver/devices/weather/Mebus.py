"""Mebus 433 MHz temperature and humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Mebus(OOKPPMDecoder):
    """Mebus 433 MHz temperature and humidity sensor."""
    name     = "Mebus-433"
    short_us = 800.0
    long_us  = 1600.0
    reset_us = 6000.0
    n_bits   = 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 40:
            return None
        b = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 40, 8))
        # Reject all-zero sync rows
        if all(x == 0 for x in b):
            return None
        address    = b[0] & 0x1F
        channel    = ((b[1] & 0x30) >> 4) + 1
        battery_ok = bool(b[1] & 0x80)
        # 12-bit signed temperature: lower nibble of b[1] as high, b[2] as low
        temp12 = ((b[1] & 0x0F) << 8) | b[2]
        if temp12 >= 2048:
            temp12 -= 4096
        temp_c   = temp12 / 10.0
        humidity = ((b[3] & 0x0F) << 4) | (b[4] >> 4)
        if not -50.0 <= temp_c <= 80.0:
            return None
        if not 0 <= humidity <= 100:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": address, "channel": channel, "battery_ok": battery_ok,
            "temperature_C": round(temp_c, 1), "humidity": humidity,
        })


__all__ = ["Mebus"]
