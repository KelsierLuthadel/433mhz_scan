"""@file
    Arad/Master Meter Dialog3G water utility meter.

    Copyright (C) 2022 avicarmeli, ProfBoc75

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Dialog3G decoder with checksum MIC.

RF information:
- FSK Manchester, ISM 915 MHz
- Message is being sent once every 30 seconds.

Data Layout:
- FF:  {8} Flags
- SS: {24} little-endian, serial number
- LL:  {8} Serial suffix
- UU:  {8} Gear/scale and volume units flags
- CC: {24} little-endian, counter value
- OO: {40} Checksum (LFSR-based, 3 bit errors can be corrected)
- TT:  {8} Trailing suffix byte
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AradMsMeter(RawDecoder):
    """Arad/Master Meter Dialog3G water utility meter.

    FSK_PULSE_MANCHESTER_ZEROBIT, chip=8.4 us, reset=100 us.
    Sync word: 0xF5138537 (32 bits).
    Payload: 128 bits (16 bytes).
    Integrity: 40-bit Galois LFSR with single/double/triple-bit error correction.
    Payload fields:
      b[0]    – flags (leak detection, typically 0x4B)
      b[1:4]  – serial number (24-bit LE BCD)
      b[4]    – serial suffix / gear (0x00, 0x27, 0x73)
      b[5]    – unit flags (0x00=m³, 0x40=L)
      b[6:9]  – counter value (24-bit LE)
      b[10]   – flags2
      b[11:16]– 40-bit LFSR checksum
    """
    name = "Arad-MS-Meter"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK Manchester demodulation and 40-bit LFSR checksum not yet implemented.
        return None


__all__ = ["AradMsMeter"]
