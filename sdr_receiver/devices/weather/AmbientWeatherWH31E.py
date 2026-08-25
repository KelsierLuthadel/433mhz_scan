"""Ambient Weather WH31E/WH31B/WH40/WN20/WS68  FSK 915 MHz (stub)."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class AmbientWeatherWH31E(RawDecoder):
    """Ambient Weather WH31E/WH31B/WH40/WN20/WS68  FSK 915 MHz (stub)."""
    name = "Ambientweather-WH31E"

    # Sync / preamble word common to all WH3x devices
    PREAMBLE = bytes([0xAA, 0x2D, 0xD4])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK demodulation requires IQ sample data not available in an OOK
        # pulse list.  Stub: return None until FSK support is added.
        return None


__all__ = ["AmbientWeatherWH31E"]
