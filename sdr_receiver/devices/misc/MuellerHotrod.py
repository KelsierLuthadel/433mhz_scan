"""Mueller Hot Rod water meter.

Copyright (C) 2024 Christian W. Zuckschwerdt <zany@triq.net>
Copyright (C) 2024 Bruno OCTAU (ProfBoc75)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Mueller Hot Rod water meter.

Both version v1 and v2 protocols look same format.

Flex decoder:

    rtl_433 -X 'n=hotrod,m=FSK_PCM,s=26,l=26,r=2500,preamble=feb100'

Data layout:
    PP PP PP YY YY YY  0  1  2  3  4  5  6  7  8  9 10 11 ...
    aa aa aa fe b1 00 II II II II GG GG GG GF CC ?? ?? ?? ...

- PP: {xx} Preamble
- YY: {24} Sync word 0xfeb100
- II: {32} Device ID
- GG: {28} 7 nibbles BCD water cumulative volume, US liquid gallon
- FF: {4} Flag, protocol version, battery_low
- CC: {8} CRC-8/UTI, poly 0x07, init 0x00, xorout 0x55
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class MuellerHotrod(RawDecoder):
    """Mueller Hot Rod water meter  FSK PCM with BCD volume."""
    name = "Mueller-HotRod"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["MuellerHotrod"]
