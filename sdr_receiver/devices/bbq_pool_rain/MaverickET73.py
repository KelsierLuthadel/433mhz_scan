"""@file
    Maverick ET-73.

    Copyright (C) 2018 Benjamin Larsson

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Maverick ET-73.

Based on TP12 code

Layout appears to be:

    II 11 12 22 XX XX

- I = random id
- 1 = temperature sensor 1 12 bits
- 2 = temperature sensor 2 12 bits
- X = unknown, checksum maybe?
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from .._helpers import _bits_to_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class MaverickET73(OOKPPMDecoder):
    """Maverick ET-73 BBQ Thermometer (dual probe).

    OOK_PULSE_PPM, 48 bits = 6 bytes.
    Layout: II 11 12 22 XX XX where I=id, 1=probe1 (12 bits), 2=probe2 (12 bits).
    """

    name     = "Maverick-ET73"
    short_us = 1050.0
    long_us  = 2050.0
    reset_us = 4400.0
    n_bits   = 48

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = _bits_to_bytes(bits[:48])
        if len(b) < 4:
            return None
        if (b[0] == 0 and b[1] == 0 and b[2] == 0 and b[3] == 0) or \
           (b[0] == 0xFF and b[1] == 0xFF and b[2] == 0xFF and b[3] == 0xFF):
            return None
        device = b[0]
        # 12-bit signed temp1: top 12 bits of bytes 1-2
        t1_raw = (b[1] << 8) | (b[2] & 0xF0)
        if t1_raw >= 0x8000:
            t1_raw -= 0x10000
        temp1_c = round((t1_raw >> 4) * 0.1, 1)
        # 12-bit signed temp2: low nibble of byte 2 + byte 3
        t2_raw = ((b[2] & 0x0F) << 12) | (b[3] << 4)
        if t2_raw >= 0x8000:
            t2_raw -= 0x10000
        temp2_c = round((t2_raw >> 4) * 0.1, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device,
            "temperature_1_C": temp1_c,
            "temperature_2_C": temp2_c,
        })


__all__ = ["MaverickET73"]
