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
- a logical 0 is represented by an HF carrier of 854.5s and 366.2s gap
- a logical 1 is represented by a 366.2s carrier and 854.5s gap
- The preamble consists of 7 to 10 * 0 and 1 * 1.

The checksums at the end are calculated as follows:
- Check: all nibbles starting with the type up to Check are XORed, result is 0
- Sum: all nibbles beginning with the type up to Check are summed up,
  5 is added and the upper 4 bits are discarded
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ElvWS2000(OOKPWMDecoder):
    """ELV WS 2000 weather station.
    OOK_PULSE_PWM, variable-length nibble frames.
    XOR of all nibbles == 0; (sum+5) & 0xF == 0 for last nibble.
    """
    name     = "ELV-WS-2000"
    short_us = 366.0
    long_us  = 854.0
    reset_us = 1000.0
    n_bits   = 40  # minimum usable frame

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        n = (len(bits) // 4) * 4
        if n < 20:
            return None
        nibbles = [bits_to_int(bits[i:i+4]) for i in range(0, n, 4)]
        xor_val = 0
        for nib in nibbles:
            xor_val ^= nib
        if xor_val != 0:
            return None
        sensor_type = nibbles[0]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "sensor_type": sensor_type,
            "nibble_count": len(nibbles),
        })


__all__ = ["ElvWS2000"]
