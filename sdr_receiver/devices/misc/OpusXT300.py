"""Opus/Imagintronix XT300 Soil Moisture Sensor.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Opus/Imagintronix XT300 Soil Moisture Sensor.

Also called XH300 sometimes, this seems to be the associated display name

https://www.plantcaretools.com/product/wireless-moisture-monitor/

Data is transmitted with 6 bytes row:

     0. 1. 2. 3. 4. 5
    FF ID SM TT ?? CC

- FF: initial preamble
- ID: 0101 01ID
- SM: soil moisture (decimal 05 -> 99 %)
- TT: temperature degC + 40degC (decimal)
- ??: always FF... maybe spare bytes
- CC: check sum (simple sum) except 0xFF preamble
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class OpusXT300(OOKPWMDecoder):
    """Opus XT300 Soil Moisture Sensor."""
    name     = "Opus-XT300"
    short_us = 544.0
    long_us  = 932.0
    reset_us = 31000.0
    n_bits   = 48

    def _parse(self, bits, freq_hz):
        if len(bits) < 48:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 48, 8)]
        if all(v == 0 for v in b):
            return None
        if b[0] != 0xFF:
            return None
        if (sum(b[1:5]) & 0xFF) != b[5]:
            return None
        channel  = b[1] & 0x03
        moisture = b[2]
        temp_c   = b[3] - 40
        if temp_c > 100 or moisture > 101:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "channel":       channel,
            "temperature_C": temp_c,
            "moisture":      moisture,
            "mic":           "CHECKSUM",
        })


__all__ = ["OpusXT300"]
