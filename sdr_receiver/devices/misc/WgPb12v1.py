"""WG-PB12V1 Temperature Sensor.

Copyright (C) 2015 Tommy Vestermark
Modifications Copyright (C) 2017 Ciarán Mooney

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

WG-PB12V1 Temperature Sensor.

Device method to decode a generic wireless temperature probe. Probe marked
with WG-PB12V1-2016/11.

Format of Packets:

The packet format appears to be similar those the Lacrosse format.
(http://fredboboss.free.fr/articles/tx29.php)

    AAAAAAAA MMMMTTTT TTTTTTTT ???IIIII HHHHHHHH CCCCCCCC

- A: Preamble - 11111111
- M: Message type?, fixed 0x3
- T: Temperature, scale 10, offset 40
- I: ID of probe, set randomly each time the device is powered off-on
- H: Humidity - not used, is always 11111111
- C: Checksum - CRC8, polynomial 0x31, initial value 0x0, final value 0x0

Temperature:

Temperature value is "deci-celsius", ie 10 dC = 1C, offset by -40 C.

    0010 01011101 = 605 dC => 60.5 C
    Remove offset => 60.5 C - 40 C = 20.5 C
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class WgPb12v1(OOKPWMDecoder):
    """WG-PB12V1 Temperature Sensor."""
    name     = "WG-PB12V1"
    short_us = 564.0
    long_us  = 1476.0
    reset_us = 2500.0
    n_bits   = 48

    def _parse(self, bits, freq_hz):
        if len(bits) < 48:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 48, 8)]
        if b[0] != 0xFF:
            return None
        if (b[1] & 0xF0) != 0x30:
            return None
        if b[4] != 0xFF:
            return None
        if crc8(bytes(b[1:5]), poly=0x31, init=0x00) != b[5]:
            return None
        probe_id = b[3] & 0x1F
        temp_raw = ((b[1] & 0x0F) << 8) | b[2]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            probe_id,
            "temperature_C": round((temp_raw - 400) * 0.1, 1),
            "mic":           "CRC",
        })


__all__ = ["WgPb12v1"]
