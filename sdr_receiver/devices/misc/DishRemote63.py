"""Decoder for UHF Dish Remote Control 6.3.

Copyright (C) 2018 David E. Tiller

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Decoder for UHF Dish Remote Control 6.3.
(tested with genuine Dish remote.)

The device uses PPM encoding,
0 is encoded as 400 us pulse and 1692 uS gap,
1 is encoded as 400 us pulse and 2812 uS gap.
The device sends 7 transmissions per button press approx 6000 uS apart.
A transmission starts with a 400 uS start bit and a 6000 uS gap.

Each packet is 16 bits in length.
Packet bits: BBBBBB10 101X1XXX
B = Button pressed, big-endian
X = unknown, possibly channel
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class DishRemote63(OOKPPMDecoder):
    """Dish Remote 6.3."""
    name     = "Dish-Remote-6.3"
    short_us = 1692.0
    long_us  = 2812.0
    reset_us = 9000.0
    n_bits   = 16

    _BUTTONS = {
        0: "Power", 1: "TV/Video", 2: "Record", 3: "DVR",
        4: "Guide", 5: "Interactive", 6: "PIP On/Off", 7: "PIP Swap",
        8: "PIP Move", 9: "PIP Ch+", 10: "PIP Ch-", 11: "Menu",
        12: "Cancel", 13: "Recall", 14: "Info", 15: "Home",
        16: "Up", 17: "Down", 18: "Left", 19: "Right", 20: "Select",
        21: "Ch+", 22: "Ch-", 23: "Vol+", 24: "Vol-", 25: "Mute",
        27: "0", 28: "1", 29: "2", 30: "3", 31: "4",
        32: "5", 33: "6", 34: "7", 35: "8", 36: "9",
        37: "Skip Back", 38: "Skip Fwd", 39: "Play",
        40: "Stop", 41: "Pause", 42: "Replay", 43: "Advance",
    }

    def _parse(self, bits, freq_hz):
        if len(bits) < 16:
            return None
        b0 = bits_to_int(bits[0:8])
        b1 = bits_to_int(bits[8:16])
        # Sanity: bits[6:8]==10 and bits[8:11]==101
        if (b0 & 0x03) != 0x02:
            return None
        if (b1 >> 5) != 0x05:
            return None
        button_code = b0 >> 2
        label = self._BUTTONS.get(button_code, f"Button-{button_code}")
        return DecodedPacket.from_fields(self.name, freq_hz,
            {"button": button_code, "label": label})


__all__ = ["DishRemote63"]
