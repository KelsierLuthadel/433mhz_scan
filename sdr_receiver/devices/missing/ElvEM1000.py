"""ELV WS 2000.

KS200/KS300 addition Copyright (C) 2022 Jan Schmidt

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

ELV WS 2000.

based on http://www.dc3yc.privat.t-online.de/protocol.htm

Protocol version V1.2

Coding of a bit:
- the length of a bit is 1220.7s, corresponding to 819.2 Hz
- it is derived from 32768 Hz : 40
- the pulse:gap ratio is 7:3 (for logical 0) or 3:7 (for logical 1)
- a logical 0 is represented by an HF carrier of 854.5s and 366.2s gap
- a logical 1 is represented by a 366.2s carrier and 854.5s gap
- The preamble consists of 7 to 10 * 0 and 1 * 1.
- The data is always transmitted as a 4-bit nibble. This is followed by a 1 bit.
- The LSBit is transmitted first.

The checksums at the end are calculated as follows:
- Check: all nibbles starting with the type up to Check are XORed, result is 0
- Sum: all nibbles beginning with the type up to Check are summed up,
  5 is added and the upper 4 bits are discarded
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ElvEM1000(OOKPPMDecoder):
    """ELV EM 1000 energy / environment monitor.
    OOK_PULSE_PPM, 72 bits (9 bytes).  XOR checksum: XOR of bytes 0-7 == byte 8.
    """
    name     = "ELV-EM-1000"
    short_us = 500.0
    long_us  = 1000.0
    reset_us = 30_000.0
    n_bits   = 72

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 72, 8))
        chk = 0
        for b in data[:8]:
            chk ^= b
        if chk != data[8]:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":          data[0],
            "device_type": data[1],
            "data_hex":    data[2:8].hex(),
        })


__all__ = ["ElvEM1000"]
