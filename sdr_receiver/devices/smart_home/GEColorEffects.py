"""GE Color Effects light-string remote decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GEColorEffects(RawDecoder):
    """GE Color Effects light-string remote.

    FSK_PULSE_PCM, chip=52 µs, reset=450 µs.
    Custom 2-bit encoding: '10'→0, '1100'→1.  17 decoded bits.
    Preamble: 5× 0xCC + 0xFF 0x00.  No checksum.
    Stub: FSK demodulation not supported in OOK pipeline.
    """
    name = "GE-ColorEffects"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK demodulation


__all__ = ["GEColorEffects"]
