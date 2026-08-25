"""Holman WS5029 / Conrad AOK-5056 / Optex 990018 (FSK PCM  stub)."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class HolmanWS5029PCM(RawDecoder):
    """Holman WS5029 / Conrad AOK-5056 / Optex 990018 (FSK PCM  stub)."""
    name = "Holman-WS5029-PCM"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK_PULSE_PCM requires IQ sample demodulation; not available in
        # the OOK pulse pipeline.  Returns None until FSK support is added.
        return None


__all__ = ["HolmanWS5029PCM"]
