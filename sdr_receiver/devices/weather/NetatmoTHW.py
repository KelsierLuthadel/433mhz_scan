"""NetAtmo Temperature/Humidity/Wind sensor  FSK PCM, stub."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class NetatmoTHW(RawDecoder):
    """NetAtmo Temperature/Humidity/Wind sensor  FSK PCM, stub."""
    name     = "NetAtmo-THW"
    PREAMBLE = bytes([0xAA, 0xAA, 0xE7, 0x12])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK IQ demodulation required; not available in the OOK pulse path.
        return None


__all__ = ["NetatmoTHW"]
