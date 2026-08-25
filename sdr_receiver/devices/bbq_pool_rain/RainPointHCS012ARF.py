"""@file
    RainPoint HCS012ARF Rain Gauge sensor.

    Copyright (C) 2021 Christian W. Zuckschwerdt <zany@triq.net>
    Copyright (C) 2025 Bruno OCTAU (ProfBoc75)

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

RainPoint HCS012ARF Rain Gauge sensor.

Manufacturer: Fujian Baldr Technology Co., Ltd
RF Information: Seen on 433.92 MHz.
FCC ID: 2AWDBHCS008FRF

Description:
- Rainfall Range: 0-9999 mm
- Accuracy: ±0.1 mm
- Data Reporting: Every 3 mins

A Transmission contains ten packets with Manchester coded data, reflected.

Data Layout:

    HH[II II II II FB FF RR RR]SS

- HH: {8} Header, fixed 0xa5
- ID: {32} Sensor ID
- FF: {6} Fixed value 0x18
- B: {1} Low Battery flag = 1, Good Battery = 0
- B: {1} Powered on = 1, then always = 0
- FF: {8} Fixed value 0x03
- RR: {16} little-endian rain gauge value, scale 10 (1 Tip = 0.1 mm)
- SS: {8} Byte sum of previous bytes except header
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPCMDecoder
from .._helpers import _bits_to_bytes, _reverse8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _manchester_decode(bits: list[int]) -> list[int] | None:
    """Decode Manchester pairs: (0,1)->0, (1,0)->1.  Returns None on error."""
    result = []
    for i in range(0, len(bits) - 1, 2):
        a, b = bits[i], bits[i + 1]
        if a == 0 and b == 1:
            result.append(0)
        elif a == 1 and b == 0:
            result.append(1)
        else:
            return None
    return result


class RainPointHCS012ARF(OOKPCMDecoder):
    """RainPoint HCS012ARF Rain Gauge Sensor.

    OOK_PULSE_PCM (chip=320 us), Manchester-encoded payload, reflected bytes.
    Header byte 0xa5, 10 bytes total.
    Checksum = sum of bytes 1-8.
    Rain in mm, scale 0.1.
    """

    name     = "RainPoint-HCS012ARF"
    chip_us  = 320.0
    reset_us = 1000.0
    n_bits   = 163  # 10 bytes × 2 × 8 chips + some preamble

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 10 * 2 * 8:
            return None
        # Manchester decode first 10 bytes worth (160 chips)
        decoded = _manchester_decode(bits[:10 * 2 * 8])
        if decoded is None or len(decoded) < 10 * 8:
            return None
        decoded = [1 - x for x in decoded]  # invert
        b = _bits_to_bytes(decoded[:10 * 8])
        if len(b) < 10:
            return None
        b = bytes(_reverse8(x) for x in b)
        if b[0] != 0xA5:
            return None
        chk_calc = sum(b[1:9]) & 0xFF
        if chk_calc != b[9]:
            return None
        id_      = (b[4] << 24) | (b[3] << 16) | (b[2] << 8) | b[1]
        flags1   = b[5]
        bat_low  = (flags1 & 0x02) >> 1
        rain_raw = (b[8] << 8) | b[7]
        rain_mm  = round(rain_raw * 0.1, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         id_,
            "battery_ok": int(not bat_low),
            "rain_mm":    rain_mm,
        })


__all__ = ["RainPointHCS012ARF"]
