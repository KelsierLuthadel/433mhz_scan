"""Govee H5112 Dual-Probe Thermometer  FSK PCM encrypted protocol (stub)."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class GoveeH5112(RawDecoder):
    """Govee H5112 Dual-Probe Thermometer  FSK PCM encrypted protocol (stub)."""
    name = "Govee-H5112"

    SYNC = bytes([0x2C, 0x4C, 0x4A])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["GoveeH5112"]
