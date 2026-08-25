"""HT680 based Remote control (broadly similar to x1527 protocol).

Copyright (C) 2016 Igor Polovnikov

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

HT680 based Remote control (broadly similar to x1527 protocol).

- short is 850 us gap 260 us pulse
- long is 434 us gap 663 us pulse
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Ht680(OOKPWMDecoder):
    """HT680 Remote Control."""
    name     = "HT680"
    short_us = 200.0
    long_us  = 600.0
    reset_us = 14000.0
    n_bits   = 41

    def _parse(self, bits, freq_hz):
        if len(bits) < 41:
            return None
        # 5 sync bits must be 10101
        if bits[0:5] != [1, 0, 1, 0, 1]:
            return None
        data = bits[5:]           # 36 data bits
        # Fixed-bit pattern validations
        if data[10:12] != [1, 0]:
            return None
        if data[13:15] != [1, 0]:
            return None
        if data[16:20] != [1, 0, 1, 0]:
            return None
        # 20-bit address from first 20 data bits
        address = bits_to_int(data[0:20])
        # 4 button states: 2-bit pairs; [1,1] = PRESSED
        btn_a = (data[20:22] == [1, 1])
        btn_b = (data[22:24] == [1, 1])
        btn_c = (data[24:26] == [1, 1])
        btn_d = (data[26:28] == [1, 1])
        # Tristate encoding of address (10 pairs of 2 bits)
        _TRI = {(0, 0): '0', (0, 1): 'Z', (1, 0): 'X', (1, 1): '1'}
        tri = ''.join(_TRI.get((data[2 * i], data[2 * i + 1]), '?')
                      for i in range(10))
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":       f"{address:05X}",
            "button_a": btn_a,
            "button_b": btn_b,
            "button_c": btn_c,
            "button_d": btn_d,
            "tristate": tri,
        })


__all__ = ["Ht680"]
