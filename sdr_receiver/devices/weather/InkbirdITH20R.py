"""Inkbird ITH-20R temperature/humidity sensor (FSK PCM  stub)."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class InkbirdITH20R(RawDecoder):
    """Inkbird ITH-20R temperature/humidity sensor (FSK PCM  stub)."""
    name = "Inkbird-ITH20R"

    PREAMBLE = bytes([0xAA, 0xAA, 0xAA, 0x2D, 0xD4])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK_PULSE_PCM requires IQ sample demodulation.  Returns None until
        # FSK support is added.
        return None


__all__ = ["InkbirdITH20R"]
