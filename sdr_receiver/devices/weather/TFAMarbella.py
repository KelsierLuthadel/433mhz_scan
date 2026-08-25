"""TFA Marbella Pool Thermometer  FSK_PULSE_PCM stub."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFAMarbella(RawDecoder):
    """TFA Marbella Pool Thermometer  FSK_PULSE_PCM stub.

    FSK PCM, chip=105 us, reset=2000 us.
    Preamble: 0xaa, 0x2d, 0xd4.  Frame: 11 bytes; byte 9 must equal 0xAA.
    Fields: serial(24 bits, bytes 3-5) | flags(8) | temp(12) | checksum(8).
    Temperature: (raw - 400) * 0.1 °C.  Battery low: byte 6 bit 7.
    Checksum: lfsr_digest8_reflect(bytes[3:10], gen=0x31, key=0xf4).
    """

    name = "TFA-Marbella"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        # Full demodulation requires FSK IQ decoding  not yet implemented.
        return None


__all__ = ["TFAMarbella"]
