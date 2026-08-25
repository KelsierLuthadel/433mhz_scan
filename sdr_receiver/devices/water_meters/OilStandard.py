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


class OilStandard(RawDecoder):
    """Oil tank monitor  standard protocol (Apollo Sonometer / generic).

    FSK_PULSE_PCM / OOK_PULSE_PCM, chip=500 us, reset=2000 us.
    Preamble: 0x55 0x5D or 0x55 0x62 (16 bits); Manchester-decoded payload follows.
    Payload: 4–5 bytes (32–40 bits after Manchester decode).  No checksum.
    Payload layout:
      bytes[0:2] – unit ID (16-bit)
      byte[2]    – flags/alarm byte; (byte[2] & 0x02) << 7 | byte[3] = 9-bit depth
      byte[3]    – depth value or binding countdown
    Valid depth: 0–305 cm.
    """
    name = "Oil-Standard"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK/OOK demodulation and Manchester decoding not yet implemented.
        return None


__all__ = ["OilStandard"]
