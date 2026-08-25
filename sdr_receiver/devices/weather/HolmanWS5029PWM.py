"""Holman Industries iWeather WS5029 (FSK PWM older variant  stub)."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class HolmanWS5029PWM(RawDecoder):
    """Holman Industries iWeather WS5029 (FSK PWM older variant  stub)."""
    name = "Holman-WS5029-PWM"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK_PULSE_PWM requires IQ sample demodulation.
        return None


__all__ = ["HolmanWS5029PWM"]
