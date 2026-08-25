"""@file
    Gasmate BA1008 meat thermometer.

    Copyright (C) 2023 Christian W. Zuckschwerdt <zany@triq.net>
    based on protocol analysis by Lucy Winters

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Gasmate BA1008 meat thermometer.

Notably this protocol does not feature ID or CHANNEL information.

S.a. #2324

Data Layout:

    PF TT ?? ?A

- P: (4 bit) preamble/model/type? fixed 0xf
- F: (4 bit) Unknown bit; Sign bit; 2-bit temperature 100ths (BCD)
- T: (8 bit) temperature 10ths and 1ths (BCD)
- ?: (12 bit) unknown value
- A: (4 bit) checksum, nibble-wide add with carry
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GasmateBA1008(OOKPPMDecoder):
    """Gasmate BA1008 wireless meat thermometer.

    Modulation: OOK_PULSE_PPM.
    Frame (32 bits):
        byte 0: preamble 0xF (bits 7-4), unused (bit 3), sign (bit 2), tenths (bits 1-0)
        byte 1: temperature BCD  upper nibble = tens, lower nibble = ones
        bytes 2-3 upper 12 bits: unknown
        byte 3 lower nibble: nibble checksum
    Checksum: sum of all 8 nibbles from the 4 bytes, masked to 4 bits, == 0xC.
    Temperature: (tens*10 + ones + tenths*0.1), negated when sign bit is set.
    """
    name     = "Gasmate-BA1008"
    short_us = 536.0
    long_us  = 1_668.0
    reset_us = 2_000.0
    n_bits   = 32

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 32:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 32, 8)]
        if (b[0] & 0xF8) != 0xF0:
            return None
        if sum((x >> 4) + (x & 0xF) for x in b) & 0xF != 0xC:
            return None
        sign   = bool((b[0] >> 2) & 1)
        tenths = b[0] & 0x03
        bcd_h  = (b[1] >> 4) * 10 + (b[1] & 0xF)
        temp_c = bcd_h + tenths * 0.1
        if sign:
            temp_c = -temp_c
        unknown = (b[2] << 4) | (b[3] >> 4)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "temperature_C": round(temp_c, 1),
            "unknown_1":     unknown,
            "mic":           "CHECKSUM",
        })


__all__ = ["GasmateBA1008"]
