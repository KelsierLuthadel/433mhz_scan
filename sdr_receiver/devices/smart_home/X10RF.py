"""X10 sensor (Non-security devices).

Copyright (C) 2015 Tommy Vestermark
Mods. by Dave Fleck 2021

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

X10 sensor decoder.

Each packet starts with a sync pulse of 9000 us (16x a bit time)
and a 4500 us gap.
The message is OOK PPM encoded with 562.5 us pulse and long gap (0 bit)
of 1687.5 us or short gap (1 bit) of 562.5 us.

There are 32bits. The message is repeated 5 times with
a packet gap of 40000 us.

The protocol has a lot of similarities to the NEC IR protocol

The second byte is the inverse of the first.
The fourth byte is the inverse of the third.

Based on protocol information found at:
http://www.wgldesigns.com/protocols/w800rf32_protocol.txt

Tested with American sensors operating at 310 MHz
e.g., rtl_433 -f 310M -R 22

Seems to work best with 2 MHz sample rate:
rtl_433 -f 310M -R 22 -s 2M

Tested with HR12A, RMS18, HD23A, MS14A, PMS03, MS12A,
RMS18, Radio Shack 61-2675-T
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


_X10_HOUSE = "ABCDEFGHIJKLMNOP"
# Device-code mapping: bit pattern → unit number
_X10_UNIT_MAP: list[int] = [13, 5, 3, 11, 15, 7, 1, 9, 14, 6, 4, 12, 16, 8, 2, 10]


class X10RF(OOKPPMDecoder):
    """X10 RF 433 MHz home-automation remote.

    OOK_PULSE_PPM, short=562 µs, long=1687 µs, reset=6000 µs.
    32 bits: bytes 0/1 and 2/3 are complementary pairs (XOR == 0xFF each).
    House code: b[0][7:4].  Unit code from b[0] and b[2].
    State: b[2] bit 5 (0=on, 1=off).  Event cmd: b[2] bit 7.
    """
    name     = "X10-RF"
    short_us = 562.0
    long_us  = 1687.0
    reset_us = 6000.0
    n_bits   = 32

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 32:
            return None
        b = [bits_to_int(bits[i : i + 8]) for i in range(0, 32, 8)]
        if (b[0] ^ b[1]) != 0xFF or (b[2] ^ b[3]) != 0xFF:
            return None
        house     = _X10_HOUSE[(b[0] >> 4) & 0xF]
        unit_idx  = (b[0] & 0x0E) | ((b[2] >> 2) & 0x01)
        unit      = _X10_UNIT_MAP[unit_idx & 0xF]
        state     = "off" if (b[2] & 0x20) else "on"
        event_cmd = bool(b[2] & 0x80)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "house": house,
            "unit":  unit,
            "state": state,
            "event": int(event_cmd),
        })


__all__ = ["X10RF"]
