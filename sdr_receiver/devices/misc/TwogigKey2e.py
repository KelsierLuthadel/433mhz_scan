"""2GIG-KEY2E-345 encrypted 4-button keyfob.

Copyright (C) 2026 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

2GIG-KEY2E-345 encrypted 4-button keyfob.

Same OOK/Manchester-zerobit family and 24-bit raw preamble (0x555556) as
the plain Honeywell/2Gig door-window sensors in honeywell.c, but a longer,
72-bit (post-preamble) frame:

    IIIIIIII IIIIIIII IIIIIIII IIIIIIII 00100101 SSSSSSSS SSSSSSSS CCCCCCCC CCCCCCCC

- I: 32 bit, believed encrypted (device id and/or rolling counter)
- 8 bit constant, 0x25 in every sample seen so far
- S: 16 bit, believed encrypted (button/status)
- C: 16 bit CRC, poly 0x8005, init 0x4c57

Reverse-engineered in issue #2584 (zuckschwerdt, klohner, dfiore1230):
CRC confirmed against 7 real codes from two different physical units.
The 32+16 encrypted bits are unsolved -- ships disabled until the payload
can be decoded.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TwogigKey2e(RawDecoder):
    """2GIG-KEY2E-345 encrypted keyfob  OOK PCM, rolling-code CRC-16."""
    name = "2GIG-KEY2E-345"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["TwogigKey2e"]
