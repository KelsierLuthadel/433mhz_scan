"""Biltema-Rain sensor.

Copyright (C) 2017 Timopen, cleanup by Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Biltema-Rain sensor.

Based on the springfield.c code, there is a lack of samples and data
thus the decoder is disabled by default.

- nibble[0] and nibble[1] is the id, changes with every reset.
- nibble[2] first bit is battery (0=OK).
- nibble[3] bit 1 is tx button pressed.
- nibble[3] bit 2 = below zero, subtract temperature with 1024. I.e. 11 bit 2's complement.
- nibble[3](bit 3 and 4) + nibble[4] + nibble[5] is the temperature in Celsius with one decimal.
- nibble[2](bit 2-4) + nibble[6] + nibble[7] is the rain rate.
- nibble[8] is checksum.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BtRain(OOKPPMDecoder):
    """Biltema rain gauge (bt_rain).
    OOK_PULSE_PPM, 36 bits, nibble-based layout.
    short gap=0, long gap=1.
    """
    name     = "Biltema-Rain-Gauge"
    short_us = 1940.0
    long_us  = 3900.0
    reset_us = 8800.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        device_id  = bits_to_int(bits[0:8])
        battery_ok = not bits[8]
        below_zero = bits[13]
        # Temperature: nibble[3] bits 14-15 (high 2) + nibble[4-5] bits 16-23 (low 8) = 10-bit raw
        temp_raw = (bits_to_int(bits[14:16]) << 8) | bits_to_int(bits[16:24])
        temp_c   = (temp_raw & 0x3FF) * 0.1 * (-1 if below_zero else 1)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "battery_ok":    int(battery_ok),
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["BtRain"]
