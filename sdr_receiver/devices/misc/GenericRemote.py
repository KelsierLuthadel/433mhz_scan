"""Generic remotes and sensors using PT2260/PT2262 SC2260/SC2262 EV1527 protocol.

Copyright (C) 2015 Tommy Vestermark
Copyright (C) 2015 nebman

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Generic remotes and sensors using PT2260/PT2262 SC2260/SC2262 EV1527 protocol.

Tested devices:
- SC2260
- EV1527
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GenericRemote(OOKPWMDecoder):
    """Generic Remote SC226x / EV1527 (25-bit fixed-code PWM remote)."""
    name     = "Generic-Remote"
    short_us = 464.0
    long_us  = 1404.0
    reset_us = 1800.0
    n_bits   = 25

    _TRI = {(0, 0): '0', (0, 1): 'Z', (1, 0): 'X', (1, 1): '1'}

    def _parse(self, bits, freq_hz):
        if len(bits) < 25:
            return None
        inv = [1 - b for b in bits]
        if inv[24] != 1:                    # MSB of final byte must be 1
            return None
        b0 = bits_to_int(inv[0:8])
        b1 = bits_to_int(inv[8:16])
        b2 = bits_to_int(inv[16:24])
        device_id = (b0 << 8) | b1
        cmd       = b2
        if device_id == 0x0000 or cmd == 0x00:
            return None
        raw24 = (b0 << 16) | (b1 << 8) | b2
        tri = ''.join(self._TRI.get(((raw24 >> (22 - 2 * i)) & 2) >> 1,
                                     (raw24 >> (22 - 2 * i)) & 1) or '?'
                      for i in range(12))
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":       device_id,
            "cmd":      cmd,
            "tristate": tri,
        })


__all__ = ["GenericRemote"]
