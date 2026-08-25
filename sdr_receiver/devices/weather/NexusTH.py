"""Nexus, FreeTec, Solight and compatible 36-bit temperature/humidity sensors."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class NexusTH(OOKPPMDecoder):
    """Nexus, FreeTec, Solight and compatible 36-bit temperature/humidity sensors."""
    name     = "Nexus-TH"
    short_us = 1000.0
    long_us  = 2000.0
    reset_us = 5000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        device_id    = bits_to_int(bits[0:8])
        battery_ok   = bool(bits[8])
        channel      = bits_to_int(bits[10:12]) + 1
        temp_raw     = bits_to_int(bits[12:24])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c       = temp_raw / 10.0
        const_nibble = bits_to_int(bits[24:28])
        if const_nibble != 0xF:
            return None
        humidity = bits_to_int(bits[28:36])
        if not 0 <= humidity <= 100:
            return None
        if not -50.0 <= temp_c <= 80.0:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id, "channel": channel, "battery_ok": battery_ok,
            "temperature_C": round(temp_c, 1), "humidity": humidity,
        })


__all__ = ["NexusTH"]
