"""mcPower Kinetic wireless switch decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class MCPowerKinetic(RawDecoder):
    """mcPower Kinetic wireless switch.

    FSK_PULSE_PCM, chip=10 µs, reset=300 µs.  Preamble: 0xaaaa (16 bits).
    48-bit payload: id[16] | buttons[8] | flags[8] | CRC-16 (poly=0x1021, init=0xaa55).
    Stub: FSK demodulation not supported in OOK pipeline.
    """
    name = "MCPower-Kinetic"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK demodulation


__all__ = ["MCPowerKinetic"]
