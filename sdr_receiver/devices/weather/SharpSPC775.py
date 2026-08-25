"""Sharp SPC775 Weather Station  FSK PWM, stub."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class SharpSPC775(RawDecoder):
    """Sharp SPC775 Weather Station  FSK PWM, stub."""
    name = "Sharp-SPC775"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK IQ demodulation required; not available in the OOK pulse path.
        return None


__all__ = ["SharpSPC775"]
