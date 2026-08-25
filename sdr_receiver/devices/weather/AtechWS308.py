"""Atech WS308 wireless temperature sensor."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class AtechWS308(RawDecoder):
    """Atech WS308 wireless temperature sensor.

    Modulation: OOK_PULSE_RZ (Return-to-Zero)
    short_us=1600, long_us=1832, reset_us=9000
    Decodes 28-bit payload via "10→0, 1110→1" run-length conversion.
    RZ modulation requires custom pulse-level decoding; stub returns None.
    """

    name = "Atech-WS308"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:  # type: ignore[override]
        return None


__all__ = ["AtechWS308"]
