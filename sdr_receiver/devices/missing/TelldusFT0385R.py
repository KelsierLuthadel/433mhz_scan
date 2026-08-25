"""Telldus weather station indoor unit FT0385R.

Copyright (C) 2021 Jarkko Sonninen <kasper@iki.fi>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Telldus weather station indoor unit.

As the indoor unit receives a message from the outdoor unit,
it sends 3 radio messages:
- Oregon-WGR800
- Oregon-THGR810 or Oregon-PCR800
- Telldus-FT0385R (this one)

The outdoor unit is the same as SwitchDoc Labs WeatherSense FT020T
and Cotech 36-7959 Weatherstation.

433Mhz, OOK modulated with Manchester encoding, halfbit-width 500 us.
Message length is 5 + 296 bit.

Integrity check is done using CRC8 using poly=0x31  init=0xc0.

Message layout:

    AAAABBBB BBBBCCCC ZJIHGFED DDDDDDDD EEEEEEEE FFFFFFFF GGGGGGGG HHHHHHHH IIIIIIII JJJJJJJJ ...

- A : 4 bit type code, fixed 0xe
- B : 8 bit indoor serial number or flags
- C : 4 bit flags, normally 0x3
- D : 9 bit Wind Avg, scaled by 10
- E : 9 bit Wind Gust, scaled by 10
- F : 9 bit Wind direction in degrees
- K : 16 bit rain rate mm, scaled by 10
- L : 16 bit Rain 1h mm, scaled by 10
- Q : 12 bit Temperature in Fahrenheit, offset 400, scaled by 10
- R : 8 bit Humidity
- S : 12 bit Temperature indoor in Fahrenheit, offset 400, scaled by 10
- T : 8 bit Humidity indoor
- U : 16 bit Pressure absolute in hPa
- Y : 8 bit CRC, poly 0x31, init 0xc0
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TelldusFT0385R(ManchesterDecoder):
    """Telldus weather station FT0385R sensors.
    OOK_PULSE_MANCHESTER_ZEROBIT, 296 bits (37 bytes).
    CRC8 poly=0x31 init=0xC0 over first 36 bytes; byte 36 = CRC.
    """
    name     = "Telldus-FT0385R"
    chip_us  = 500.0
    reset_us = 2400.0
    n_bits   = 296

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 296:
            return None
        data = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 296, 8))
        if crc8(data[:36], poly=0x31, init=0xC0) != data[36]:
            return None
        # Sequential field extraction
        idx = [0]

        def take(n: int) -> int:
            v = bits_to_int(bits[idx[0]:idx[0]+n])
            idx[0] += n
            return v

        wind_avg     = take(9)   # tenths m/s
        wind_gust    = take(9)
        wind_dir     = take(9)   # degrees / 2
        rain         = take(16)  # tenths mm
        temp_out_raw = take(12)  # tenths degC + 400 offset
        hum_out      = take(8)
        temp_in_raw  = take(12)
        hum_in       = take(8)
        pressure     = take(16)  # tenths hPa
        light        = take(16)
        uv           = take(8)

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "wind_avg_m_s":    wind_avg / 10.0,
            "wind_gust_m_s":   wind_gust / 10.0,
            "wind_dir_deg":    wind_dir * 2,
            "rain_mm":         rain / 10.0,
            "temperature_C":   (temp_out_raw - 400) / 10.0,
            "humidity":        hum_out,
            "temperature_in_C": (temp_in_raw - 400) / 10.0,
            "humidity_in":     hum_in,
            "pressure_hPa":    pressure / 10.0,
            "light_lux":       light,
            "uv_index":        uv,
        })


__all__ = ["TelldusFT0385R"]
