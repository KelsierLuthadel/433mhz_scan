"""Emax W6 / Altronics X7063/4A / Optex 990040 Weather Station  FSK, stub."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class EmaxW6(RawDecoder):
    """Emax W6 / Altronics X7063/4A / Optex 990040 Weather Station  FSK, stub."""
    name     = "Emax-W6"
    PREAMBLE = bytes([0xAA, 0xAA, 0xCA, 0xCA, 0x54])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK IQ demodulation required; not available in the OOK pulse path.
        return None


__all__ = ["EmaxW6"]
