"""Prologue / FreeTec NC-7104 / NC-7159-675 temperature sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Prologue(OOKPPMDecoder):
    """Prologue / FreeTec NC-7104 / NC-7159-675 temperature sensor."""
    name     = "Prologue"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 10000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        sensor_type = bits_to_int(bits[0:4])
        if sensor_type not in (0x9, 0x5):
            return None
        device_id  = bits_to_int(bits[4:12])
        battery_ok = bool(bits[12])
        button     = bool(bits[13])
        channel    = bits_to_int(bits[14:16]) + 1
        temp_raw   = bits_to_int(bits[16:28])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c   = temp_raw / 10.0
        humidity = bits_to_int(bits[28:36])
        fields: dict = {
            "id": device_id, "channel": channel, "battery_ok": battery_ok,
            "button": button, "temperature_C": round(temp_c, 1),
        }
        if humidity != 0xCC:
            fields["humidity"] = humidity
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["Prologue"]
