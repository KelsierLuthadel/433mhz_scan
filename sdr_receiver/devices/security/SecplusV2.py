"""Security+ 2.0 rolling code.

Copyright (C) 2020 Peter Shipley <peter.shipley@gmail.com>
Based on code by Clayton Smith https://github.com/argilo/secplus

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Security+ 2.0 rolling code.

Data comes in two bursts/packets.

Layout:

    bits = `AA BB OOOO IIII X*30`

- AA = payload type  (2 bits 00 or 01)
- BB = FrameID (2 bits always 00)
- OOOO = Order indicator (4 bits)
- IIII = inversion indicator (4 bits).
- XXXX....  = data (30 bits)

data is broken up into 3 parts (p0 p1 p2)
eg:

data = `ABCABCABCABCABCABCABCABCABCABC`
becomes:

    `p0 = AAAAAAAAAA`
    `p1 = BBBBBBBBBB`
    `p2 = CCCCCCCCCC`

these three parts are then inverted and reordered based on the 4bit Order and Inversion indicators

fixed generated from concatenate  p0 + p1

roll_array is generated from the 8 bit used for Order and Inversion indicators + p3
by reading the buffer in binary bit pairs forming trinary values

EG:
`1 0 0 1 1 0 1 0 0 1 1 0=> [1 0] [0 1] [1 0] [1 0] [0 1] [1 0] => 2 1 2 2 1 2`

Returns data in :
  * roll_array as an array of trinary values  0, 1, 2) the value 3 is invalid
  * fixed_p as a bitbuffer_t with 20 bits of data

Once the above has been run twice the two are merged.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SecplusV2(RawDecoder):
    """Chamberlain / LiftMaster Security+ v2.0 (OOK_PULSE_PCM, 250 µs chip).

    Two-half Manchester-decoded protocol with deinterleave, inversion,
    reorder, and trinary rolling code (800 ms inter-packet window).
    """

    name = "Secplus-V2"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["SecplusV2"]
