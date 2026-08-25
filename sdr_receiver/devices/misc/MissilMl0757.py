"""Missil ML0757 weather station with temperature, wind and rain sensor.

Copyright (C) 2020 Marius Lindvall

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Missil ML0757 weather station with temperature, wind and rain sensor.

The unit sends two different alternating packets, one for temperature and one
for rainfall and wind. All packets are 40 bits and are transferred 9 times.

Packet structure:

                         BIT
          0   1   2   3   4   5   6   7   8
      0x0 +---+---+---+---+---+---+---+---+
          | Device ID                     |
      0x1 +---+---+---+---+---+---+---+---+
    B     |BAT| ? | ? | ? | ? |RWP| ? | ? | <-- FLAGS BYTE
    Y 0x2 +---+---+---+---+---+---+---+---+
    T     | Data field 1                 >|
    E 0x3 +---+---+---+---+---+---+---+---+
          |<Data field 1  | Data field 2 >|
      0x4 +---+---+---+---+---+---+---+---+
          |<Data field 2  | 1 | 1 | 1 | 1 |
      0x5 +---+---+---+---+---+---+---+---+

When flag bit RWP is not set, data field 1 is (temp in degC * 10) as a signed
12-bit integer, and data field 2 (8 bits) is unknown.

When bit RWP is set, data field 1 is accumulated rainfall in steps as a signed
12-bit integer (each step = 0.45 mm of rain). Data field 2 is wind speed as an
8 bit integer: 0x00 = calm, 0x80 = medium, 0xC0 = strong.

The BAT flag is set if the transmitter has low battery.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class MissilMl0757(OOKPPMDecoder):
    """Missil ML0757 weather station."""
    name     = "Missil-ML0757"
    short_us = 975.0
    long_us  = 1950.0
    reset_us = 4500.0
    n_bits   = 40

    def _parse(self, bits, freq_hz):
        if len(bits) < 40:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8)]
        if (b[4] & 0x0F) != 0x0F:          # last 4 bits must be 1111
            return None
        device_id = b[0]
        flags     = b[1]
        bat_low   = bool(flags & 0x80)
        rwp       = bool(flags & 0x04)
        raw12     = ((b[2] << 4) | (b[3] >> 4)) & 0xFFF
        raw8      = ((b[3] & 0x0F) << 4) | (b[4] >> 4)
        fields: dict = {"id": device_id, "battery_low": bat_low}
        if not rwp:
            if raw12 >= 2048:
                raw12 -= 4096
            fields["temperature_C"] = round(raw12 * 0.1, 1)
        else:
            fields["rainfall_mm"] = round(raw12 * 0.45, 2)
            wind_map = {0x00: "calm", 0x80: "medium", 0xC0: "strong"}
            fields["wind_speed"] = wind_map.get(raw8, f"0x{raw8:02X}")
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["MissilMl0757"]
