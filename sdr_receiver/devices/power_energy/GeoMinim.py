"""@file
    GEO mimim+ energy monitor.

    Copyright (C) 2022 Lawrence Rust, lvr at softsystem dot co dot uk

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

GEO mimim+ energy monitor.

The GEO minim+ energy monitor comprises a sensor unit and a display unit.
https://assets.geotogether.com/sites/4/20170719152420/Minim-Data-sheet.pdf

Frequency 868.29 MHz, bit period 25 microseconds (40kbps), modulation FSK_PCM.

Packet types determined by length byte (offset 3):
  0x05 → CT sensor packet (11 bytes):
      bytes 0-2 : device ID (24-bit)
      bytes 4-5 : instantaneous power (13-bit × VA, bit 6 adds 5 VA offset)
      bytes 6-8 : uptime in ~8-second intervals (24-bit)
  0x2A → Display unit packet (48 bytes):
      bytes 0-2 : device ID
      bytes 4-5 : power (15-bit × 5 W)
      bytes 14-15: energy last 15 min (11-bit Wh)
      bytes 30-33: datetime (day count from 2007-01-01, hours, minutes)
CRC-16 poly 0x8005.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GeoMinim(RawDecoder):
    """GEO minim+ energy monitor (FSK_PULSE_PCM, ~41.7 kbps).

    Preamble: 0xAAAA7BB9 or 0x55557BB9.
    Two packet types determined by length byte (offset 3):
        0x05 → CT sensor packet (11 bytes):
            bytes 0-2 : device ID (24-bit)
            bytes 4-5 : instantaneous power (13-bit × VA, bit 6 adds 5 VA offset)
            bytes 6-8 : uptime in ~8-second intervals (24-bit)
        0x2A → Display unit packet (48 bytes):
            bytes 0-2 : device ID
            bytes 4-5 : power (15-bit × 5 W)
            bytes 14-15: energy last 15 min (11-bit Wh)
            bytes 30-33: datetime (day count from 2007-01-01, hours, minutes)
    CRC-16 poly 0x8005.
    """
    name = "GEO-minim"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["GeoMinim"]
