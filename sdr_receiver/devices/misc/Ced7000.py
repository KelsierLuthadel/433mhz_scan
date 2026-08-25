"""CED7000 Shot Timer

Copyright (C) 2023 Pierros Papadeas <pierros@papadeas.gr>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

CED7000 Shot Timer, also CED8000.

FSK_PCM with 1300 us short, 1300 us long, and 3500 us gap.
Sync is a 0xaa4d5e, then payload.
The data is repeated 3 times.

Data layout:

    II II CC FF FF FS SS SS UU UU U

- I: RFID, 16 bit LSB, reversed in order, decimal representation per 4 bits, 4 digits
- C: shot counter, 8 bit LSB, reversed in order, decimal representation per 4 bits, 2 digits
- F: final time, 20 bit LSB, reversed in order, decimal representation per 4 bits, 5 digits with 2 decimal points assumed
- S: split time, 20 bit LSB, reversed in order, decimal representation per 4 bits, 5 digits with 2 decimal points assumed
- U: unknown 20 bits, possible checksum and ending sync word
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Ced7000(RawDecoder):
    """CED7000 Shot Timer  FSK PCM with Manchester encoding."""
    name = "CED7000"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["Ced7000"]
