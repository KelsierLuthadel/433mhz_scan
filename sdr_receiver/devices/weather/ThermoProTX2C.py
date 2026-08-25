"""ThermoPro TX-2C Outdoor Thermometer and Humidity Sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ThermoProTX2C(OOKPPMDecoder):
    """ThermoPro TX-2C Outdoor Thermometer and Humidity Sensor.

    OOK PPM, 36 bits (longer frames include 12-bit zero trailer up to 45 bits).
    No checksum; trailing-zero check omitted when only 36 bits are received.
    Layout: type[4] | id[8] | flags[4] | temp[12] | humidity[8]
    """

    name     = "Thermopro-TX2C"
    short_us = 1958.0
    long_us  = 3825.0
    reset_us = 8643.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        b     = [bits_to_int(bits[i * 8:(i + 1) * 8]) for i in range(4)]
        b4_hi = bits_to_int(bits[32:36])  # upper nibble of humidity

        if (not any(b)) or all(x == 0xFF for x in b):
            return None

        id_     = ((b[0] & 0xF) << 4) | (b[1] >> 4)
        battery = (b[1] & 0x08) >> 3   # 1 = low battery
        button  = (b[1] & 0x04) >> 2
        channel = (b[1] & 0x03) + 1

        # 12-bit signed temperature
        raw16 = (b[2] << 8) | b[3]
        if raw16 >= 0x8000:
            raw16 -= 0x10000
        temp_c = (raw16 >> 4) * 0.1

        humidity = ((b[3] & 0xF) << 4) | b4_hi

        fields: dict = {
            "id": id_,
            "channel": channel,
            "battery_ok": int(not battery),
            "temperature_C": round(temp_c, 1),
            "button": button,
        }
        if humidity != 0x0A:
            fields["humidity"] = humidity
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["ThermoProTX2C"]
