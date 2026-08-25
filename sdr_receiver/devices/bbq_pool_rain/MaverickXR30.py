"""Maverick XR-30 BBQ Sensor  ported from rtl_433 C source.

Note: maverick.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class MaverickXR30(RawDecoder):
    """Maverick XR-30 BBQ Sensor (stub  FSK_PULSE_PCM, not decodable in OOK pipeline).

    Sync word 0xd391d391; payload: FLAG:4h T1:10d T2:10d DIGEST:16h.
    Requires FSK demodulation; returns None in OOK capture mode.
    """

    name = "Maverick-XR30"

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        return None  # FSK_PULSE_PCM  requires FSK demodulation


__all__ = ["MaverickXR30"]
