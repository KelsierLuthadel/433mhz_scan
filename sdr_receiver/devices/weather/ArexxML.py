"""Arexx Multilogger temperature/humidity sensor (TL-3TSN, SHT-10, TSN-70E)."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class ArexxML(RawDecoder):
    """Arexx Multilogger temperature/humidity sensor (TL-3TSN, SHT-10, TSN-70E).

    Modulation: FSK_PULSE_MANCHESTER_ZEROBIT at 2400 bps
    chip_us=208, reset_us=450
    Preamble 0xAA 0xAA 0x55 followed by inverted payload; CRC-8 poly=0x31.
    FSK modulation is not supported by OOK base classes; stub.
    """

    name = "Arexx-ML"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:  # type: ignore[override]
        return None


__all__ = ["ArexxML"]
