"""Oria WA150KM Freezer/Fridge Thermometer  PCM+Manchester, stub."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class OriaWA150KM(RawDecoder):
    """Oria WA150KM Freezer/Fridge Thermometer  PCM+Manchester, stub."""
    name = "Oria-WA150KM"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # PCM + Manchester + Oregon nibble CRC not yet implemented.
        return None


__all__ = ["OriaWA150KM"]
