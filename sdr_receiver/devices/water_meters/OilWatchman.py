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


class OilWatchman(RawDecoder):
    """Watchman Sonic / Apollo Ultrasonic / Beckett Rocket oil tank monitor.

    FSK_PULSE_PCM, chip=1000 us, reset=4000 us.
    Preamble: 0b111000xx (6-bit pattern); Manchester-decoded payload follows.
    Payload: 8 bytes (64 bits after Manchester decode).
    CRC-8 LE poly=0x31 init=0x00 over bytes[0:7]; stored in byte[7].
    Payload layout:
      bytes[0:4] – unit ID (32-bit)
      byte[4]    – status flags (rebinding, alarm)
      byte[5]    – temperature factor + depth MSBs
      byte[6]    – depth LSBs or binding countdown
      byte[7]    – CRC-8 LE
    """
    name = "Oil-Watchman"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK demodulation and Manchester decoding not yet implemented.
        return None


__all__ = ["OilWatchman"]
