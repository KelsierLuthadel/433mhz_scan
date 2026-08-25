"""Decoder for EN2058 (FSK_PCM, 100 us bit width).

Copyright (C) 2026 Steven Walter

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Decoder for EN2058 four probe temperature sensor.

The device uses FSK-PCM modulation with a fixed 100 us bit width
(short_width = long_width = 100 us).

Data layout:

    PPPP aa aa aa aa aa ca ca III TT TT TT TT aa CC ffff...ffff SS SS ffff

- P: 30 bit preamble (15 1-bits, 15 0-bits)
- a/c: fixed bytes, always observed as shown
- I: 24 bit device identifier
- T: 16 bit temperature, repeated 4x, offset 900, scale 10, degrees Fahrenheit.
  A disconnected probe reads a fixed sentinel value.
- a: fixed byte, always observed as 0xaa
- C: 8 bit checksum
- f: 144 bit fixed filler, always observed as a 00-17 (hex) counting sequence
- S: 8 bit sequence counter, sent twice back to back, increments by 2 each repeat
- f: 20 bit fixed filler

The data is then repeated nine times, back to back with no pause between one
repeat's filler and the next preamble.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class En2058(RawDecoder):
    """EN2058 four probe temperature sensor  FSK PCM, 194-bit repeating frame."""
    name = "EN2058"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["En2058"]
