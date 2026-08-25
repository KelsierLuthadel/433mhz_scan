"""Philips outdoor temperature sensor.

Copyright (C) 2018 Nicolas Jourden <nicolas.jourden@laposte.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Philips outdoor temperature sensor -- used with various Philips clock
radios (tested on AJ7010).
This is inspired from the other Philips driver made by Chris Coffey.

A complete message is 40 bits:
- 3 times sync of 1000us pulse + 1000us gap.
- 40 bits, 2000 us short or 6000 us long
- packet gap is 38 ms
- Packets are repeated 3 times.

Data format is:

    00000000  0ccccccc tttttttt TTTTTTTT XXXXXXXX

- c: 7 bit channel: 0x5A=channel 1, 0x45=channel 2, 0x36=channel 3
- t: 16 bit temperature in ADC value that is then converted to deg. C.
- X: XOR sum, every 2nd packet without last data byte (T).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class PhilipsAJ7010(OOKPWMDecoder):
    """Philips outdoor temperature sensor (AJ7010)."""
    name     = "Philips-AJ7010"
    short_us = 2000.0
    long_us  = 6000.0
    reset_us = 30000.0
    n_bits   = 40

    _CH_MAP = {0x5A: 1, 0x45: 2, 0x36: 3}

    def _parse(self, bits, freq_hz):
        if len(bits) < 40:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8)]
        if b[0] != 0x00:
            return None
        ch = self._CH_MAP.get(b[1])
        if ch is None:
            return None
        if (b[0] ^ b[1] ^ b[2] ^ b[3]) != b[4]:
            return None
        raw_temp = ((b[2] << 8) | b[3]) & 0x3FFF
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "channel":       ch,
            "temperature_C": round(raw_temp / 353.0 - 9.2, 1),
            "mic":           "CHECKSUM",
        })


__all__ = ["PhilipsAJ7010"]
