"""RFM69 decoder as used on LowPowerLabs Moteino boards.

Copyright (C) 2025 Ian Cockett <cockettian@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Generic decoder for RFM69 radio modules as used on LowPowerLab.com Moteino boards.

    rtl_433 -s 1000k

Test data captured with sample sketch https://github.com/LowPowerLab/RFM69/blob/master/Examples/Node/Node.ino

Encryption must be disabled in the sketch (comment out #define ENCRYPTKEY)
Data captures from 433MHz RFM69HW_HCW board, but 868MHz models should be similar.

Protocol description:

- Preamble    aaaaaa
- Sync word   2d64
- Header byte 1 - Length Byte
- Header byte 2 - Dest Address
- Header byte 3 - Src Address
- Header byte 4 - Control byte
- n bytes variable length message.
- CRC16 checksum
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Rfm69Moteino(RawDecoder):
    """RFM69 LowPowerLab Moteino  FSK PCM with CRC-16."""
    name = "RFM69-Moteino"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["Rfm69Moteino"]
