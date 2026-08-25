"""@file
    Badger ORION water meter support.

    Copyright (C) 2022 Nicko van Someren

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Badger ORION water meter.

S.a. https://fccid.io/GIF2006B

For the single-frequency models the center frequency is 916.45MHz. The bit rate is
100KHz, so the sample rate should be at least 1.2MHz.

The low-level encoding is much the same as M-Bus mode T, but the payload differs.

The data is preceded by several sync bytes of 01010101, followed by the ten bit
preamble of 0000 1111 01. This is followed by 10 bytes encoded using a 4:6 NRZ
encoding.

Once decoded, the format is:
- Device ID: 3 bytes, little-endian.
- Device flags: 1 byte.
- Meter reading: 3 bytes, little-endian. Value in gallons.
- Status flags: 1 byte.
- CRC: 2 bytes, crc16, polynomial 0x3D65
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BadgerWater(RawDecoder):
    """Badger ORION water meter (EZ / standard endpoint).

    FSK_PULSE_PCM, chip=10 us, reset=1000 us.
    Preamble: 0x54 0x3D (16 bits).
    4:6 NRZ encoding; decoded payload: 10 bytes.
      bytes[0:3]  – device ID (24-bit LE)
      byte[3]     – flags_1
      bytes[4:7]  – volume in gallons (24-bit LE)
      byte[7]     – flags_2
      bytes[8:10] – CRC-16 (poly=0x3D65, inverted)
    """
    name = "Badger-Water"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK demodulation and 4:6 NRZ decoding not yet implemented.
        return None


__all__ = ["BadgerWater"]
