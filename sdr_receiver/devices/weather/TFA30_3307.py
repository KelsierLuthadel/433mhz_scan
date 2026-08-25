"""TFA 30.3307.02 Wind sensor  OOK_PULSE_RZI with G3RUH descrambling stub."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFA30_3307(RawDecoder):
    """TFA 30.3307.02 Wind sensor  OOK_PULSE_RZI with G3RUH descrambling stub.

    OOK RZI, short=30 us, long=167 us, reset=500 us.
    Processing chain: differential PSK → differential NRZS → G3RUH descramble.
    Sync word: 0x4b2dd42b.  Payload: 1-byte length + 6-byte device ID + data + CRC-32.
    Wind fields: direction(4 bits × 22.5°), speed(9 bits × 0.1 m/s), gust(9 bits × 0.1 m/s).
    CRC-32: poly=0x04c11db7, init=0xe7720ae4.
    """

    name = "TFA-303307"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        # Requires differential PSK + NRZS decoding and G3RUH descrambling  not yet implemented.
        return None


__all__ = ["TFA30_3307"]
