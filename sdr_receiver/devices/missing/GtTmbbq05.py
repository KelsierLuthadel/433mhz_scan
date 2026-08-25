"""Globaltronics Quigg BBQ GT-TMBBQ-05.

Copyright (C) 2019 Olaf Glage

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Globaltronics Quigg BBQ GT-TMBBQ-05.

BBQ thermometer sold at Aldi (germany).
Simple device, no possibility to select channel. Single temperature measurement.

The temperature is transmitted in Fahrenheit with an addon of 90. Accuracy is 10 bit. No decimals.
One data row contains 33 bits and is repeated 8 times. Each followed by a 0-row.
First bit seem to be a static 0. By ignoring this we get nice byte boundaries.
Next 8 bits are static per device (even after battery change).
Next 8 bits contain the lower 8 bits of the temperature.
Next 8 bits are static per device (even after battery change).
Next 2 bits contain the upper 2 bits of the temperature.
Next 1 bit is unknown.
Next 1 bit is an odd parity bit.
Last 4 bits are the sum of the preceding 5 nibbles (mod 0xf).

Frame structure:
    Byte:   H 1        2        3        4
    Type:   0 SSSSSSSS tttttttt ssssssss TT?Pcccc

- S: static per device (even after battery change)
- t: temperature+90 F lower 8 bits
- s: static per device (even after battery change)
- T: temperature+90 F upper 2 bits
- P: odd parity bit
- c: sum of first 5 nibbles
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GtTmbbq05(OOKPPMDecoder):
    """Globaltronics QUIGG GT-TMBBQ-05 BBQ thermometer.
    OOK_PULSE_PPM, 33 bits; leading bit is sync  discard it.
    Temperature stored as 10-bit raw: temp_F = (raw - 90) / 10.
    """
    name     = "Globaltronics-GT-TMBBQ05"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 9100.0
    n_bits   = 33

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bits[1:]  # discard leading sync bit
        if len(b) < 32:
            return None
        static_id = bits_to_int(b[0:8])
        temp_low  = bits_to_int(b[8:16])
        temp_hi2  = bits_to_int(b[24:26])   # upper 2 bits of 10-bit temp
        temp_raw  = (temp_hi2 << 8) | temp_low
        temp_f    = (temp_raw - 90) / 10.0
        temp_c    = (temp_f - 32.0) / 1.8
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            static_id,
            "temperature_F": round(temp_f, 1),
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["GtTmbbq05"]
