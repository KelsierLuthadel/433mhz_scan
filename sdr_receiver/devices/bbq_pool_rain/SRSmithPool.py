"""SR Smith Pool Light Remote Control SRS-2C-TX  ported from rtl_433 C source.

Note: sr_smith_pool.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SRSmithPool(RawDecoder):
    """SR Smith Pool Light Remote Control SRS-2C-TX (stub  FSK at 915 MHz).

    Sync 0xd391d391; payload: SIZE(8) UNKNOWN(32) PIN(8) BUTTON(8) CRC8(8) CRC16(16).
    Requires FSK demodulation at 915 MHz; returns None in OOK capture mode.
    """

    name = "SRSmith-SRS2CTX"

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        return None  # FSK_PULSE_PCM at 915 MHz  requires FSK demodulation


__all__ = ["SRSmithPool"]
