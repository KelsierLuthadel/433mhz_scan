"""Arad/Master Meter Dialog3G water utility meter.

Copyright (C) 2022 avicarmeli, ProfBoc75

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Dialog3G decoder with checksum MIC.

Optional parameters:
- serials=SER1;SER2;SER3-SUFFIX
- gear=0.01|0.1|1|10|100
- units=m3|l|cf|usg

The serial filter is optional.
Gear and units may be overridden when auto detection is not reliable enough.
Up to 3 payload bit errors are corrected using the checksum syndrome.

RF information:
- FSK Manchester, ISM 915 Mhz
- Message is being sent once every 30 seconds.

Data Layout, payload in square brackets:

    Byte Position                                 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
    Sample         00 00 00 00 3e 69 0a ec 7a c8 4b 47 f7 2e 00 40 5f 25 00 00 0c 9e c5 cb 55 38 f8
                   00 00 00 00 UU UU UU UU UU UU[FF SS SS SS LL UU CC CC CC ?? ?F]OO OO OO OO OO TT

- 00:  {?} Preamble
- UU: {48} UID, sync word, always 0x3e690aec7ac8
- FF:  {8} Flags
- SS: {24} little-endian, serial number
- LL:  {8} Serial suffix
- UU:  {8} Gear/scale and volume units flags
- CC: {24} little-endian, counter value
- OO: {40} Checksum
- TT:  {8} Trailing suffix byte
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AradMsMeter(RawDecoder):
    """Arad/Master Meter Dialog3G water utility meter  FSK Manchester, LFSR CRC."""
    name = "Arad-MsMeter"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["AradMsMeter"]
