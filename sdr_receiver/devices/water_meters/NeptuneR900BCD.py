"""Neptune R900 BCD flow meter decoder.

Same PCM encoding as Neptune R900 (chip=30 us, reset=320 us,
preamble 0x55 0x55 0x55 0xa9 0x66 0x69 0x65) but the 24-bit
consumption field is BCD-encoded: every nibble must be 0-9.
Frames where any consumption nibble is outside 0-9 are rejected
so the two decoders are mutually exclusive.

Stub: base-6 nibble-to-binary conversion not yet implemented.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class NeptuneR900BCD(RawDecoder):
    """Neptune R900 BCD flow meters (OOK_PULSE_PCM, chip=30 us, reset=320 us)."""
    name = "Neptune-R900BCD"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: base-6 PCM decoding shared with NeptuneR900 not yet implemented.
        # BCD variant: all consumption nibbles (bits[48:72]) must be 0-9.
        return None


__all__ = ["NeptuneR900BCD"]
