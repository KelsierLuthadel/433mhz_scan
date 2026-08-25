"""@file
    Apator Metra E-RM 30 Water Meters.

    Copyright (C) 2025 Alex Carp (@carpalex)
    Copyright (c) 2026 Bruno Octau (@ProfBoc75)

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Apator Metra E-RM 30 Water Meters.

S.a issue #3012, for E-RM 30, #3452, for E-ITN 30

Both E-RM 30 (Water Meter) and E-ITN 30 (Heat Cost Allocator) use the same approach
and protocol. Only the message length differs.

Coding:
- Frames transmitted with preamble (0xaa 0xaa ...), followed by the 0x699a syncword.
- 2 levels of data coding: IBM whitening, then nibble-substitution decryption.
- Each message: one byte payload length, encrypted payload, 2 byte CRC-16.
- Payload length: 19 bytes for water meter, 17 bytes for heat meter.
- CRC-16 must be checked after unwhitening and before decrypting the payload.

E-RM 30 Payload fields:
- I  32b: little-endian, id, visible on the radio module
- V  25b: little-endian, volume in liters (or scale 1000 in m3)
- D  16b: little-endian, date: Year (offset 2000) {7} Month {4} Day {5}
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ApatorMetraErm30(RawDecoder):
    """Apator Metra E-RM 30 water meter.

    FSK_PULSE_PCM, chip=25 us, reset=5000 us.
    Preamble: 0xaa 0xaa 0x69 0x9a (sync word 0x699a).
    IBM whitening XOR with 22-byte key, then CRC-16/ARC (poly=0x8005, init=0xFFFF),
    then nibble-substitution decryption.
    Frame: 22 bytes (1 length + 19 payload + 2 CRC).
    Payload fields (after decrypt):
      bytes[0:4]   – device ID (32-bit LE, XOR 0x30000000)
      bytes[4:8]   – volume (25-bit LE, >> 3, / 1000 → m³)
      bytes[15:17] – date LE (day 5b, month 4b, year-2000 7b)
    """
    name = "ApatorMetra-ERM30"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK demodulation, IBM whitening, and nibble-decryption not yet implemented.
        return None


__all__ = ["ApatorMetraErm30"]
