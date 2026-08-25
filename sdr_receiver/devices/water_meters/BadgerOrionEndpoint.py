"""@file
    Orion Water Endpoint Meter.

    Copyright (C) 2025 Bruno OCTAU (@ProfBoc75), @klyubin

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Orion Water Endpoint Meter.

Manufacturer: Badger Meter Inc
FCCID: GIF2014W-OSE

Frequency Hopping Spread Spectrum, 902-928 MHz band.
2 Hopping options: Fixed Mode (50 channels, 904.56-924.56 MHz) or Mobile Mode
(48 channels, 904.45-923.675 MHz). Frequency channel changed every 150 seconds.

Message is encoded using IBM Whitening Algorithm.

Data Layout:
- LL: {8} Message length
- II: {32} Fixed value (reverse flow counter?)
- SS: {32} Serial Number, little-endian
- RR: {32} Reading value, scale 10 gallon, little-endian
- DD: {32} Daily Reading Value, scale 10 gallon, little-endian
- CC: {16} CRC-16, poly 0x8005, init 0xFFFF
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BadgerOrionEndpoint(RawDecoder):
    """Badger ORION endpoint water meter (GIF2014W-OSE and GIF2020OCECNA).

    FSK_PULSE_PCM; chip=10 us (2014 model) or 5 us (2020 model), reset=1000 us.
    Preamble: 0xaa 0xaa 0xec 0x62 0xec 0x62 (48 bits).
    IBM whitening XOR with 23-byte key, CRC-16/ARC (poly=0x8005, init=0xFFFF).
    Payload: 23 bytes.
      bytes[5:9]   – serial ID (32-bit LE)
      bytes[9:12]  – model/battery/status flags
      byte[10] bit5– leak flag
      bytes[12:16] – reading (10-gallon units)
      bytes[16:20] – daily reading (10-gallon units)
      bytes[21:23] – CRC
    """
    name = "Badger-ORION-Endpoint"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK demodulation and IBM whitening not yet implemented.
        return None


__all__ = ["BadgerOrionEndpoint"]
