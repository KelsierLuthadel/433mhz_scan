"""Sainlogic SA8 / Gevanti SA8 Weather Station  UART PCM, stub."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class SainlogicSA8(RawDecoder):
    """Sainlogic SA8 / Gevanti SA8 Weather Station  UART PCM, stub."""
    name     = "Sainlogic-SA8"
    PREAMBLE = bytes([0xFC, 0x95])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # UART 8-N-1 extraction from OOK-PCM bitstream not yet implemented.
        return None


__all__ = ["SainlogicSA8"]
