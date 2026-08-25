"""Govee H5310 Pool/Spa Thermometer  FSK PCM encrypted protocol (stub)."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class GoveeH5310(RawDecoder):
    """Govee H5310 Pool/Spa Thermometer  FSK PCM encrypted protocol (stub)."""
    name = "Govee-H5310"

    SYNC = bytes([0x2C, 0x4C, 0x4A])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["GoveeH5310"]
