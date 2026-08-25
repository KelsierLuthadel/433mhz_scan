"""Brennenstuhl RCS 2044 remote control on 433.92MHz likely x1527.

Copyright (C) 2015 Paul Ortyl

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BrennenstuhlRCS2044(OOKPWMDecoder):
    """Brennenstuhl RCS 2044 mains socket remote.

    OOK_PULSE_PWM, short=320 µs, long=968 µs, reset=4000 µs.
    25 bits: even-indexed bits are padding (= 1); data bits at odd indices.
    12 data bits: system_code[5] | key_row[5] | on_off[2].
    Valid key_row values: 0x10 A, 0x08 B, 0x04 C, 0x02 D, 0x01 E.
    Valid on_off: 0x02 ON, 0x01 OFF.  No checksum.
    """
    name     = "Brennenstuhl-RCS2044"
    short_us = 320.0
    long_us  = 968.0
    reset_us = 4000.0
    n_bits   = 25

    _KEY_NAMES: dict[int, str] = {
        0x10: "A", 0x08: "B", 0x04: "C", 0x02: "D", 0x01: "E"
    }

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 25:
            return None
        # even positions (0,2,4,...) must be 1 padding
        for i in range(0, 25, 2):
            if bits[i] != 1:
                return None
        data = [bits[i] for i in range(1, 25, 2)]   # 12 data bits at odd positions
        sys_code = bits_to_int(data[0:5])
        key_row  = bits_to_int(data[5:10])
        on_off   = bits_to_int(data[10:12])
        key_name = self._KEY_NAMES.get(key_row)
        if key_name is None or on_off not in (0x01, 0x02):
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "system_code": sys_code,
            "key": key_name,
            "state": "on" if on_off == 0x02 else "off",
        })


__all__ = ["BrennenstuhlRCS2044"]
