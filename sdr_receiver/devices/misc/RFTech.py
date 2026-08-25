"""RF-tech decoder (INFRA 217S34).

Copyright (C) 2016 Erik Johannessen

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

RF-tech decoder (INFRA 217S34).

Also marked INFRA 217S34
Ewig Industries Macao

Example of message:

    01001001 00011010 00000100

- First byte is unknown, but probably id.
- Second byte is the integer part of the temperature.
- Third byte bits 0-3 is the fraction/tenths of the temperature.
- Third byte bit 7 is 1 with fresh batteries.
- Third byte bit 6 is 1 on button press.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class RFTech(OOKPPMDecoder):
    """RF-tech temperature/button sensor."""
    name     = "RF-tech"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 10000.0
    n_bits   = 24

    def _parse(self, bits, freq_hz):
        if len(bits) < 24:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 24, 8)]
        sensor_id  = b[0]
        temp_int   = b[1] & 0x7F
        temp_neg   = bool(b[1] & 0x80)
        temp_frac  = (b[2] & 0x0F) * 0.1
        temp_c     = -(temp_int + temp_frac) if temp_neg else (temp_int + temp_frac)
        battery_ok = bool(b[2] & 0x80)
        button     = bool(b[2] & 0x60)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "battery_ok":   battery_ok,
            "temperature_C": round(temp_c, 1),
            "button":        button,
        })


__all__ = ["RFTech"]
