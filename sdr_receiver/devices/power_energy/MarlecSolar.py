"""@file
    Decoder for Marlec Solar iBoost+ devices.

    Copyright (C) 2021 Christian W. Zuckschwerdt <zany@triq.net>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Decoder for Marlec Solar iBoost+ devices.

Note: work in progress, very similar to Archos-TBH.

- Modulation: FSK PCM
- Frequency: 868.3MHz
- 20 us bit time
- based on TI CC1100

Payload format:
- Preamble          {32} 0xaaaaaaaa
- Syncword          {32} 0xd391d391
- Length            {8}
- Payload           {n}
- Checksum          {16} CRC16 poly=0x8005 init=0xffff

Usual payload lengths seem to be 37 (0x25), 105 (0x69), 66 (0x42).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class MarlecSolar(RawDecoder):
    """Marlec Solar iBoost+ hot-water diverter monitor (FSK_PULSE_PCM, 50 kbps).

    Preamble : 0xAAAAAAAA
    Syncword : 0xD391D391
    Frame    : variable length (max 105 bytes), CRC-16 (poly 0x8005, init 0xFFFF).
    Key fields:
        boost_time  : minutes remaining (byte 6)
        solar_off   : bool (byte 7)
        tank_hot    : bool (byte 8)
        battery_low : bool (byte 13)
        heating     : 16-bit signed watts (bytes 17-18)
        import_val  : 32-bit Wh import today (bytes 19-22)
        saved_today / yesterday / last_7 / last_28 / total : 32-bit Wh each
    """
    name = "Marlec-Solar"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["MarlecSolar"]
