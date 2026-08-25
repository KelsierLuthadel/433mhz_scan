"""Decoder for Linear Megacode Garage & Gate Remotes.

Copyright (C) 2021 Aaron Spangler <aaron777@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Decoder for Linear Megacode Garage & Gate Remotes. (Fixed/non-rolling code).

A Linear Megacode transmission consists of 24 bit frames starting with the
most significant bit and ending with the least. Each of the 24 bit frames is
6 milliseconds wide and always contains a single 1 millisecond pulse. A frame
with more than 1 pulse or a frame with no pulse is invalid and a receiver
should reset and begin watching for another start bit.

The position of the pulse within the bit frame determines if it represents a
binary 0 or binary 1. If the pulse is within the first half of the frame, it
represents binary 0. The second half of the frame represents a binary 1.

References:
- https://github.com/aaronsp777/megadecoder/blob/main/Protocol.md
- https://wiki.cuvoodoo.info/doku.php?id=megacode
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Megacode(RawDecoder):
    """Linear Megacode Garage/Gate Remote  OOK PCM pulse-position encoding."""
    name = "Megacode"

    def decode(self, pulses, freq_hz):
        # Pulse-position modulation within 6 ms frames requires
        # raw pulse-timing analysis not available in the bit pipeline.
        return None


__all__ = ["Megacode"]
