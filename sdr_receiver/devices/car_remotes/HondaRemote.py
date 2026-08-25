"""Honda Car Key  FSK PWM, ~390-bit frame.

Stub: protocol uses FSK_PULSE_PWM.  Frame markers: bytes 0 and 38 must
be 0xFF.  Device ID at bytes 44-45; command at byte 46 (value - 0xAA).
No checksum.  Device is disabled in rtl_433 (no MIC, weak sanity checks).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HondaRemote(RawDecoder):
    """Honda Car Key (early model)  FSK PWM, ~390-bit frame.

    Stub: protocol uses FSK_PULSE_PWM.  Frame markers: bytes 0 and 38 must
    be 0xFF.  Device ID at bytes 44-45; command at byte 46 (value - 0xAA).
    No checksum.  Device is disabled in rtl_433 (no MIC, weak sanity checks).
    """
    name = "Honda Car Key"
    # FSK_PULSE_PWM: short=250 µs, long=500 µs, reset=2000 µs

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK demodulation is not supported by the OOK base classes.
        return None


__all__ = ["HondaRemote"]
