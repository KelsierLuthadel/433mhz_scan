"""ThermoPro TX-2 Temperature / Humidity Sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ThermoProTX2(OOKPPMDecoder):
    """ThermoPro TX-2 Temperature / Humidity Sensor.

    OOK PPM, 36 bits.  No checksum (collision-avoidance via type nibble).
    Also compatible with Prologue sensors (type nibble 0x9 or 0x5).
    Layout: type[4] | id[8] | flags[4] | temp[12] | humidity[8]
    """

    name     = "Thermopro-TX2"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 10000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        b0    = bits_to_int(bits[0:8])
        b1    = bits_to_int(bits[8:16])
        b2    = bits_to_int(bits[16:24])
        b3    = bits_to_int(bits[24:32])
        b4_hi = bits_to_int(bits[32:36])  # upper nibble of humidity

        type_nibble = b0 >> 4
        if type_nibble not in (0x9, 0x5):
            return None

        id_     = ((b0 & 0x0F) << 4) | ((b1 & 0xF0) >> 4)
        battery = bool(b1 & 0x08)   # 1 = low battery
        button  = (b1 & 0x04) >> 2
        channel = (b1 & 0x03) + 1

        # 12-bit signed temperature (C sign-extends 16-bit then shifts right 4)
        raw16 = (b2 << 8) | (b3 & 0xF0)
        if raw16 >= 0x8000:
            raw16 -= 0x10000
        temp_c = (raw16 >> 4) * 0.1

        humidity = ((b3 & 0x0F) << 4) | b4_hi

        fields: dict = {
            "subtype": type_nibble,
            "id": id_,
            "channel": channel,
            "battery_ok": int(not battery),
            "temperature_C": round(temp_c, 2),
            "button": button,
        }
        if humidity != 0xCC:
            fields["humidity"] = humidity
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["ThermoProTX2"]
