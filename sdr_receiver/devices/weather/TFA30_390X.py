"""TFA Dostmann 30.390X T/H sensors series  FSK_PULSE_PCM stub."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFA30_390X(RawDecoder):
    """TFA Dostmann 30.390X T/H sensors series  FSK_PULSE_PCM stub.

    FSK PCM, chip=61 us, tolerance=5, reset=3500 us (868.025 MHz).
    Sync word: 0x4b2dd42b.  Frame lengths: 24, 30, or 36 bytes.
    Payload: length(1) + device_id(4) + status(1) + counter(2) + sensor_data + CRC-32.
    CRC-32: poly=0x04c11db7, reflected, init/xorout=0xffffffff.
    Temperature: sign-extended 11-bit (or 12-bit external) × 0.1 °C.
    """

    name = "TFA-30.390X"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        # Full demodulation requires FSK IQ decoding  not yet implemented.
        return None


__all__ = ["TFA30_390X"]
