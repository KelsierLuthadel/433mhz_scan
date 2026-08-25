"""Florabest FB-TH-1 BBQ Thermometer.

Copyright (C) 2026 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Florabest FB-TH-1 BBQ Thermometer (Lidl), also sold as other Florabest
grill thermometers with a wireless remote display.

Reverse engineered from captures posted in
https://github.com/merbanan/rtl_433/issues/1223.

The sensor sends 30 bits, OOK PPM modulated, repeated about 9 times with
a longer sync gap between repeats.

    .short_width = 2000 us (0 bit)
    .long_width  = 4000 us (1 bit)
    .sync gap    = 9000 us

Layout:

    II II TT TT

- I: 16 bit, observed fixed on the one unit tested (0x4909); unconfirmed
  whether this is a true per-device id or a fixed model/sync code
- T: 16 bit, top 13 bits are the temperature, bit 29 (the very last bit)
  is a parity bit

The 13-bit temperature is a raw value scaled and offset in Fahrenheit,
observed empirically (not from a datasheet), with some inherent
imprecision reported by the original analysis:

    temp_F = raw13 * 0.1 - 90

Integrity check: XOR of all 30 bits (including the parity bit itself) is
always 1 (odd parity) on every capture seen so far.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class FlorabBest(OOKPPMDecoder):
    """Florabest FB-TH-1 BBQ / oven thermometer.

    OOK_PULSE_PPM, short=2000 µs, long=4000 µs, reset=11000 µs.
    30 bits: id[16] | temp_raw[13] | parity[1].
    temp_F = temp_raw * 0.1 − 90.  Parity: XOR of all 30 bits == 1 (odd).
    """
    name     = "Florabest-BBQ"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 11000.0
    n_bits   = 30

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 30:
            return None
        # odd parity: XOR of all 30 bits must be 1
        xval = 0
        for b in bits[:30]:
            xval ^= b
        if xval != 1:
            return None
        device_id = bits_to_int(bits[0:16])
        temp_raw  = bits_to_int(bits[16:29])
        temp_f    = temp_raw * 0.1 - 90.0
        temp_c    = (temp_f - 32.0) / 1.8
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "temperature_F": round(temp_f, 1),
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["FlorabBest"]
