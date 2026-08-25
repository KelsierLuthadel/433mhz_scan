"""Thermor A6N 132TX temperature sensor.

Copyright (C) 2020 Jon Klixbuell Langeland

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Thermor A6N 132TX temperature sensor.

FCC: https://fccid.io/A6N-132TX

32-bit frame, repeated 11 times (require 5 identical versions).

Data layout:

    IIIICC-- TTTTTTTT TTTTTTTT CCCCCCCC

- I: 4 bit ID
- C: 2 bit channel
- -: 2 bit unknown
- T: 16 bit temperature, stored as int / 10 (e.g. 376 = 37.6C), valid up to 250C
- C: 8 bit checksum

Checksum algorithm:
- Low nibble: sum of low nibbles of bytes 0-2, mod 16
- High nibble: ID-specific

Sample data:

    3c 01 7f 3c : 38.3C
    3c 01 88 a5 : 39.2C
    50 01 0c bd : 26.8C

Flex decoder:

    rtl_433 -X 'n=thermor_a6n_132tx,m=OOK_PPM,s=1000,l=2000,g=2000,r=4000,repeats>=5'
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ThermorA6N132TX(OOKPPMDecoder):
    """Thermor A6N 132TX temperature sensor.
    OOK_PULSE_PPM, 32 bits: ID(4) Channel(2) Reserved(2) Temp(16) CRC(8).
    Checksum: low-nibble sum of first 6 nibbles mod 16 == CRC low nibble.
    """
    name     = "Thermor-A6N-132TX"
    short_us = 1000.0
    long_us  = 2000.0
    reset_us = 4000.0
    n_bits   = 32

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        device_id = bits_to_int(bits[0:4])
        channel   = bits_to_int(bits[4:6]) + 1
        temp_raw  = bits_to_int(bits[8:24])
        checksum  = bits_to_int(bits[24:32])
        # Low-nibble sum check
        nib_sum = sum(bits_to_int(bits[i:i+4]) for i in range(0, 24, 4)) & 0xF
        if nib_sum != (checksum & 0xF):
            return None
        # Signed 16-bit temperature in tenths of degC
        if temp_raw & 0x8000:
            temp_c = (temp_raw - 0x10000) / 10.0
        else:
            temp_c = temp_raw / 10.0
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["ThermorA6N132TX"]
