"""Silvercrest remote decoder.

Copyright (C) 2018 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Silvercrest remote decoder.

@todo Documentation needed.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


# Silvercrest button-command lookup table (cmd index → expected check nibble)
_SILVERCREST_LUT: list[int] = [
    0x08, 0x04, 0x02, 0x01, 0x0b, 0x07, 0x05, 0x03,
    0x0a, 0x09, 0x06, 0x0c, 0x0f, 0x0e, 0x0d, 0x0c,
]


class Silvercrest(OOKPWMDecoder):
    """Silvercrest remote control (LIDL).

    OOK_PULSE_PWM, short=264 µs, long=744 µs, reset=12000 µs.
    33 bits; byte 0 = 0x7C, byte 1 = 0x26 (sync), byte 2 low-nibble = cmd,
    byte 3 low-nibble = check via LUT.
    """
    name     = "Silvercrest-Remote"
    short_us = 264.0
    long_us  = 744.0
    reset_us = 12000.0
    n_bits   = 33

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 33:
            return None
        b = [bits_to_int(bits[i : i + 8]) for i in range(0, 32, 8)]
        if b[0] != 0x7C or b[1] != 0x26:
            return None
        cmd = b[2] & 0x0F
        chk = b[3] & 0x0F
        if _SILVERCREST_LUT[cmd] != chk:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {"button": cmd})


__all__ = ["Silvercrest"]
