"""Homelead HG9901 soil moisture/temp/light level sensor decoder.

Copyright (C) 2025 Boing <dhs.mobil@gmail.com>, @inonoob
and Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Homelead HG9901 soil moisture/temp/light level sensor decoder.

- Shenzhen Homelead Electronics Co., LTD. Wireless Soil Monitor HG9901
  FCC ID: 2AAXF-HG9901

Known rebrands:
- Geevon T23033 / T230302 Soil Moisture/Temp/Light Level Sensor
- Dr.Meter soil sensor
- Royal Gardineer ZX8859-944
- Various other rebrands: Reyke, Vodeson, Midlocater, Kithouse, Vingnut

Data Layout:

        PPPP PPPP PPPP PPPP IIII IIII IIII IIII MMMM MMMM STTT TTTT QQBB LLLL CCCC XXXXXXXX

- P = Preamble of 16 bits with 0xaa55 (inverted)
- I = ID 16 bits
- M = soil moisture 0-100% as an 8 bit integer
- S = sign for temperature (0 for positive or 1 for negative)
- T = Temperature as 7 bit integer
- Q = 2 sequence bits
- B = battery status 1 (1.22 V) to 3 (above 1.42 V)
- L = light level (9 states from LOW- to HIGH+)
- C = 4 bit checksum
- X = Trailer of 8 bits equal to 0xf8

9 repeats of 433.92 MHz (EU region).
Modulation is OOK PWM with 400/1200 us timing, inverted bits.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HomeleadHG9901(OOKPWMDecoder):
    """Homelead HG9901 / Geevon / Dr.Meter / Royal Gardineer soil sensor.
    OOK_PULSE_PWM, 65 bits: 16-bit preamble + 49 data bits.
    Nibble-sum checksum (4 bits) over 10 data nibbles.
    """
    name     = "Homelead-HG9901"
    short_us = 432.0
    long_us  = 1228.0
    reset_us = 4500.0
    n_bits   = 65

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 65:
            return None
        b = bits[16:]  # skip 16-bit preamble
        device_id = bits_to_int(b[0:16])
        moisture  = bits_to_int(b[16:24])
        sign      = b[24]
        temp_raw  = bits_to_int(b[25:32])
        temp_c    = -temp_raw if sign else temp_raw
        battery   = bits_to_int(b[34:36])
        light     = bits_to_int(b[36:40])
        checksum  = bits_to_int(b[40:44])
        # Nibble-sum over 10 nibbles (bits 0-39 of payload)
        calc_chk = sum(bits_to_int(b[i:i+4]) for i in range(0, 40, 4)) & 0xF
        if calc_chk != checksum:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "moisture":      moisture,
            "temperature_C": temp_c,
            "battery":       battery,
            "light":         light,
        })


__all__ = ["HomeleadHG9901"]
