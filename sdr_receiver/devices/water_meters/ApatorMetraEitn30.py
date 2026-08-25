"""@file
    Apator Metra E-ITN 30 Heat cost allocator.

    Copyright (C) 2025 Alex Carp (@carpalex)
    Copyright (c) 2026 Bruno Octau (@ProfBoc75)

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Apator Metra E-ITN 30 Heat cost allocator.

S.a issue #3012, for E-RM 30, #3452, for E-ITN 30

Both E-RM 30 (Water Meter) and E-ITN 30 (Heat Cost Allocator) use the same approach
and protocol. Only the message length differs.

Coding:
- Frames transmitted with preamble (0xaa 0xaa ...), followed by the 0x699a syncword.
- 2 levels of data coding: IBM whitening, then nibble-substitution decryption.
- Each message: one byte payload length, encrypted payload, 2 byte CRC-16.
- Payload length: 19 bytes for water meter, 17 bytes for heat meter.
- CRC-16 must be checked after unwhitening and before decrypting the payload.

Payload fields (after decrypt):
- II: {25} little endian, serial number of the sensor
- PP: {16} little endian, last year value
- VV: {16} little endian, current value
- MDYY: {16} little endian, current date (YEAR offset 2000 {7} MONTH {4} DAY {5})
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ApatorMetraEitn30(RawDecoder):
    """Apator Metra E-ITN 30 heat cost allocator.

    FSK_PULSE_PCM, chip=25 us, reset=5000 us.
    Preamble: 0xaa 0xaa 0x69 0x9a (sync word 0x699a).
    IBM whitening XOR with 22-byte key, then CRC-16/ARC (poly=0x8005, init=0xFFFF),
    then nibble-substitution decryption.
    Frame: 1 length byte + 17 payload bytes + 2 CRC bytes = 20 bytes.
    Payload fields (after decrypt):
      bytes[0:4]   – serial ID (25-bit LE, XOR 0x38000000)
      bytes[4:6]   – previous-year heating value (16-bit LE)
      bytes[10:12] – current heating value (16-bit LE)
      bytes[12:14] – date LE (year-2000 7b, month 4b, day 5b)
    """
    name = "ApatorMetra-EITN30"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK demodulation, IBM whitening, and nibble-decryption not yet implemented.
        return None


__all__ = ["ApatorMetraEitn30"]
