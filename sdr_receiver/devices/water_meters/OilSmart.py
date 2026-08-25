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


class OilSmart(RawDecoder):
    """Oil ultrasonic SMART FSK oil tank level sensor.

    FSK_PULSE_PCM, chip=500 us, gap=2000 us, reset=9000 us.
    Preamble: 0x55 0x58 (16 bits); Manchester-decoded payload follows.
    Payload: 8 bytes (64 bits after Manchester decode).
    CRC-8 poly=0x31 init=0x00 bit-reflected over all 8 bytes.
    Payload layout:
      bytes[0:4] – sensor ID (32-bit)
      byte[4]    – status: fixed(1b), txstatus(1b), temp_ok(2b), fixed(1b), battery_ok(1b), sensor(2b)
      byte[5]    – fixed(1b), counter(3b), unknown(3b), depth_msb(1b)
      byte[6]    – depth_lsb (8 bits); depth = (b5[0] << 8) | b6 in cm
      byte[7]    – CRC-8
    """
    name = "Oil-Smart"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK demodulation and Manchester decoding not yet implemented.
        return None


__all__ = ["OilSmart"]
