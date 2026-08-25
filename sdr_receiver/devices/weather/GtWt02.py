"""Globaltronics GT-WT-02 temperature and humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GtWt02(OOKPPMDecoder):
    """Globaltronics GT-WT-02 temperature and humidity sensor."""
    name     = "GT-WT-02"
    short_us = 2500.0
    long_us  = 5000.0
    reset_us = 12000.0
    n_bits   = 37

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 37:
            return None
        device_id  = bits_to_int(bits[0:8])
        battery_ok = not bool(bits[8])
        button     = bool(bits[9])
        channel    = bits_to_int(bits[10:12]) + 1
        temp_raw   = bits_to_int(bits[12:24])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c   = temp_raw / 10.0
        humidity = bits_to_int(bits[24:31])
        checksum = bits_to_int(bits[31:37])
        # Checksum: sum of 8 nibbles (bits[0:32]) mod 64
        nibbles = [bits_to_int(bits[i:i+4]) for i in range(0, 32, 4)]
        if sum(nibbles) % 64 != checksum:
            return None
        if not -20.0 <= temp_c <= 60.0:
            return None
        # Sentinel humidity values: 10→0%, 110→100%
        if humidity == 10:
            humidity = 0
        elif humidity == 110:
            humidity = 100
        elif not 20 <= humidity <= 90:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id, "channel": channel, "battery_ok": battery_ok,
            "button": button,
            "temperature_C": round(temp_c, 1), "humidity": humidity,
        })


__all__ = ["GtWt02"]
