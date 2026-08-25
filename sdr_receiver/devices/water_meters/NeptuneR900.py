"""@file
    Neptune R900 flow meter decoder.

    Copyright (C) 2022 Jeffrey S. Ruby

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Neptune R900 flow meter decoder.

The product site lists E-CODER R900 and MACH10 R900.

The device uses PPM encoding,
- 1 is encoded as 30 us pulse.
- 0 is encoded as 30 us gap.

A gap longer than 320 us is considered the end of the transmission.

Preamble: 0xAA,0xAA,0xAA,0xAB,0x52,0xCC,0xD2

Once the payload is decoded, the message is as follows:
- ID - 32 bits
- Unkn1 - 8 bits (upper nibble), Meter type - 4 bits (lower nibble of byte 4)
- NoUse - 6 bits
- BackFlow - 2 bits
- Consumption - 24 bits (1/10 gallon units)
- Wrap - 3 bits (high bits of Consumption)
- Leak - 4 bits (days of leak mapping)
- LeakNow - 2 bits
- Extra - 24 bits
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class NeptuneR900(RawDecoder):
    """Neptune R900 flow meters.

    OOK_PULSE_PCM, chip=30 us, reset=320 us.
    Preamble: 0x55 0x55 0x55 0xa9 0x66 0x69 0x65 (56 bits).
    Base-6 encoded: 168 bits → 104 bits (13 bytes) after base-6 conversion.
    No checksum.
    Payload fields (13 bytes):
      bytes[0:4]  – meter ID (32-bit LE)
      nibble[8]   – unknown1 (4 bits)
      nibble[9]   – meter type (4 bits)
      bits[40:43] – unknown2 (3 bits)
      bits[43:46] – no-use (3 bits)
      bits[46:48] – backflow (2 bits)
      bits[48:75] – consumption (27 bits: 24 + 3-bit wrap)
      bits[75:78] – leak (3 bits)
      bits[78:80] – leaknow (2 bits)
      bits[80:104]– extra (24 bits)
    """
    name = "Neptune-R900"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: base-6 nibble-to-binary conversion not yet implemented.
        return None


__all__ = ["NeptuneR900"]
