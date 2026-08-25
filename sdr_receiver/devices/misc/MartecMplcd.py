"""Decoder for Martec MPLCD ceiling fan remotes

Copyright (C) 2024 Don Ashdown

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Decoder for Martec MPLCD ceiling fan remotes

Remote keeps knowledge of fan state and sends combined light and fan setting on each button press.

Data layout:

    22 bits
    PPPP IIII DDDDDDD SS U CCCC

- P: 4 bit fixed preamble 0x8
- I: 4 bit channel ID - reflected and inverted
- D: 7 bit dimmer - 0 is off, 1-41 is on with 1 being full brightness
- S: 2 bit speed - 0: off, 1: high, 2: medium, 3: low
- U: 1 bit unknown
- C: 4 bit simple checksum

Checksum is simple sum over 4 nibbles starting from bit 2

See https://github.com/merbanan/rtl_433/pull/3133
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class MartecMplcd(OOKPWMDecoder):
    """Martec MPLCD Ceiling Fan Remote."""
    name     = "Martec-MPLCD"
    short_us = 292.0
    long_us  = 648.0
    reset_us = 12000.0
    n_bits   = 22

    _SPEEDS = {0: "off", 1: "high", 2: "medium", 3: "low"}

    def _parse(self, bits, freq_hz):
        if len(bits) < 22:
            return None
        # Preamble nibble at bits[0:4] must be 0x8
        if bits_to_int(bits[0:4]) != 0x8:
            return None
        # Reject trivially-zero payload
        if bits[0:10] == [0] * 10:
            return None
        # Checksum: sum of 4 nibbles starting at bit 2
        n0 = bits_to_int(bits[2:6])
        n1 = bits_to_int(bits[6:10])
        n2 = bits_to_int(bits[10:14])
        n3 = bits_to_int(bits[14:18])
        chk_calc = (n0 + n1 + n2 + n3) & 0xF
        chk_recv = bits_to_int(bits[18:22])
        if chk_calc != chk_recv:
            return None
        # Channel ID at bits 4-7: reflect bit order then invert
        raw_id   = bits_to_int(bits[4:8])
        reflected = int(f"{raw_id:04b}"[::-1], 2)
        channel  = (~reflected) & 0xF
        dimmer   = bits_to_int(bits[8:15])
        speed    = bits_to_int(bits[15:17])
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "channel":   channel,
            "dimmer":    dimmer,
            "fan_speed": self._SPEEDS.get(speed, str(speed)),
            "mic":       "CHECKSUM",
        })


__all__ = ["MartecMplcd"]
