"""TFA Dostmann 14.1504.V2 grill/meat thermometer  FSK_PULSE_PCM stub."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFA14_1504_V2(RawDecoder):
    """TFA Dostmann 14.1504.V2 grill/meat thermometer  FSK_PULSE_PCM stub.

    FSK PCM, chip=360 us, reset=4096 us.
    Preamble: 0xaaaa5c (24 bits).  Payload: 40 bits (5 bytes).
    Fields: flags(4) | temperature(12) | separator=0xff(8) | digest16(16).
    Digest: LFSR-16 poly=0x8810 init=0x0d42, XOR 0x16eb.
    """

    name = "TFA-14.1504.V2"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        # Full demodulation requires FSK IQ decoding  not yet implemented.
        return None


__all__ = ["TFA14_1504_V2"]
