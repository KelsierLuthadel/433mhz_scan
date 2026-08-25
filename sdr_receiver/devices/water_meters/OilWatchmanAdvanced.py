"""@file
    Oil tank monitor using Si4320 framed FSK protocol.

    Copyright (C) 2015 David Woodhouse

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Oil tank monitor using Si4320 framed FSK protocol.

Tested devices:
- Sensor Systems Watchman Sonic
- Kingspan Watchman Sonic Plus
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class OilWatchmanAdvanced(RawDecoder):
    """Watchman Sonic Advanced / Plus / Tekelek oil tank monitor.

    FSK_PULSE_PCM (GFSK), chip=500 us, reset=12500 us.
    Packet: 192 bits total.
      40-bit preamble (0xaa repeating)
      16-bit sync 0x2DD4
       8-bit length 0x0E (14 bytes)
     128-bit body
    CRC-16/ARC (poly=0x8005, init=0x0000) over 15 bytes.
    Body layout:
      bytes[0:2]  – model (0x0401, 0x0106, 0x0101)
      bytes[2:5]  – serial number (24-bit)
      byte[5]     – status flags
      byte[6]     – temperature: (value − 0x48) × 0.5 °C
      byte[7]     – raw sensor reading
      bytes[8:10] – 12-bit depth (cm)
      bytes[10:14]– version constant 0x01050300
      bytes[14:16]– CRC-16
    """
    name = "Oil-WatchmanAdv"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: GFSK demodulation not yet implemented.
        return None


__all__ = ["OilWatchmanAdvanced"]
