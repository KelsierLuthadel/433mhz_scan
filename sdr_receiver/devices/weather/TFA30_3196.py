"""TFA Dostmann 30.3196 T/H outdoor sensor  FSK_PULSE_MANCHESTER_ZEROBIT stub."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFA30_3196(RawDecoder):
    """TFA Dostmann 30.3196 T/H outdoor sensor  FSK_PULSE_MANCHESTER_ZEROBIT stub.

    FSK Manchester, chip=245 us, reset=22000 us.
    48-bit payload + 12-bit preamble (0x55/0x56).
    Fields: type=0xa8(8) | channel(2) | temp(12) | battery+humidity(8) | digest16(16).
    Temperature: (raw - 400) * 0.1 °C.
    Checksum: LFSR-16 digest, poly=0x8810, key=0x22d0.
    """

    name = "TFA-303196"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        # Full demodulation requires FSK IQ decoding  not yet implemented.
        return None


__all__ = ["TFA30_3196"]
