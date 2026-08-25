"""Decoder for Regency fan remotes.

Copyright (C) 2020-2022 David E. Tiller

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Decoder for Regency fan remotes.

Regency fans use OOK_PULSE_PPM encoding.
The packet starts with 576 uS start pulse.
- 0 is defined as a 375 uS gap followed by a 970 uS pulse.
- 1 is defined as a 880 uS gap followed by a 450 uS pulse.

Transmissions consist of the start bit followed by bursts of 20 bits,
repeated up to 11 times; 4 identical repeats are required to decode.

As written, the PPM code always interprets a narrow gap as a 1 and a
long gap as a 0, however the actual data over the air is inverted,
i.e. a short gap is a 0 and a long gap is a 1. In addition, the data
is 5 nibbles long and is represented in Little-Endian format. In the
code I invert the bits and also reflect the bytes. Reflection introduces
an additional nibble at bit offsets 16-19, so the data is expressed a 3
complete bytes.

Packet layout:

     Bit number
     0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23
      CHANNEL  |  COMMAND  |            VALUE       | 0  0  0  0| 4 bit checksum

The CHECKSUM is calculated by adding the nibbles of the first two bytes
and ANDing the result with 0x0f.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _reflect(val: int, n: int) -> int:
    """Bit-reverse the lowest *n* bits of *val*."""
    result = 0
    for _ in range(n):
        result = (result << 1) | (val & 1)
        val >>= 1
    return result


class RegencyFan(OOKPWMDecoder):
    """Regency ceiling fan remote.

    OOK_PULSE_PWM, short=580 µs, long=976 µs, reset=14000 µs.
    21 bits: start[1] | data[20].  Data bytes are reflected before use.
    Fields: channel[4] | command[4] | value[8].
    Checksum: sum of both nibbles of bytes 0-1, ANDed with 0x0F == b2[7:4].
    """
    name     = "Regency-Fan"
    short_us = 580.0
    long_us  = 976.0
    reset_us = 14000.0
    n_bits   = 21

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 21:
            return None
        data = bits[1:21]   # skip start bit
        b0   = _reflect(bits_to_int(data[0:8]),  8)
        b1   = _reflect(bits_to_int(data[8:16]), 8)
        b2   = _reflect(bits_to_int(data[16:20] + [0, 0, 0, 0]), 8)
        chk_rx  = (b2 >> 4) & 0xF
        chk_exp = ((b0 >> 4) + (b0 & 0xF) + (b1 >> 4) + (b1 & 0xF)) & 0xF
        if chk_rx != chk_exp:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "channel": (b0 >> 4) & 0xF,
            "command": b0 & 0xF,
            "value":   b1,
        })


__all__ = ["RegencyFan"]
