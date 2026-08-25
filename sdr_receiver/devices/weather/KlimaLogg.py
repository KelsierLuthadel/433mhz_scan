"""TFA KlimaLogg temperature/humidity base-station receiver."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class KlimaLogg(RawDecoder):
    """TFA KlimaLogg temperature/humidity base-station receiver.

    Modulation: OOK_PULSE_NRZS (NRZ-Space differential encoding)
    short_us=26, reset_us=1000
    2-byte sync 0xB4 0x2B + 9 data bytes; CRC-8 poly=0x31.
    NRZS differential encoding is not supported by OOK base classes; stub.
    """

    name = "KlimaLogg"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:  # type: ignore[override]
        return None


__all__ = ["KlimaLogg"]
