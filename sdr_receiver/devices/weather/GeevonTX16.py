"""Geevon TX16-3 outdoor temperature/humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GeevonTX16(OOKPWMDecoder):
    """Geevon TX16-3 outdoor temperature/humidity sensor."""
    name     = "Geevon-TX16"
    short_us = 250.0
    long_us  = 500.0
    reset_us = 1_700.0
    n_bits   = 73

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 73:
            return None
        # Take 72 bits (9 bytes); bit 73 is sync padding
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 72, 8))

        # CRC-8 residue check over all 9 bytes
        if crc8(b, poly=0x31, init=0x7B) != 0:
            return None

        battery_low = (b[1] >> 7) & 1
        channel     = ((b[1] & 0x30) >> 4) + 1
        temp_raw    = (b[2] << 4) | (b[3] >> 4)
        temp_c      = (temp_raw - 500) * 0.1
        humidity    = b[4]

        if not -50.0 <= temp_c <= 80.0:
            return None
        if not 0 <= humidity <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            b[0],
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["GeevonTX16"]
