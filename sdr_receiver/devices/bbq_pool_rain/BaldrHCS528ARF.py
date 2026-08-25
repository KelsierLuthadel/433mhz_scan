"""@file
    Baldr HCS528ARF Pool Thermometer sensor.

    Copyright (C) 2025 Bruno OCTAU, Christian W. Zuckschwerdt, @endmarsfr

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Baldr HCS528ARF Pool Thermometer sensor.

Brand: Fujian Baldr Technology Co., Ltd.
Reference: Baldr HCS528ARF Pool Thermometer sensor works with Baldr HCS015T2H Display Station

S.a. Issue 3333

OOK PCM, MC, Invert and Reflect, the message is repeated 10 times.
The protocol is very similar to Rainpoint HCS012ARF, here 11 bytes instead of 10.

Data Layout (before reflect):

    SS II II II II FB FF TT TF FF CC T

- SS: {8}  0xa5, header sync word
- II: {48} Sensor ID
- B1: {1}  Low Battery flag = 1, Good Battery = 0
- B2: {1}  Powered on = 1, then always = 0
- TT: {12} Temperature, Fahrenheit, scale 10
- CC: {8}  Checksum, addition of previous reflected bytes except sync word.
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


class BaldrHCS528ARF(OOKPCMDecoder):
    """Baldr HCS528ARF Pool Thermometer Sensor.

    OOK_PULSE_PCM (chip=320 us), Manchester-encoded payload, reflected bytes.
    11 bytes total; header sync 0xa5.
    Checksum = sum of bytes 1-9.
    Temperature in Fahrenheit, scale 0.1, from 12-bit little-endian field.
    """

    name     = "Baldr-HCS528ARF"
    chip_us  = 320.0
    reset_us = 1000.0
    n_bits   = 179  # 11 bytes × 2 × 8 chips

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 11 * 2 * 8:
            return None
        decoded = _manchester_decode(bits[:11 * 2 * 8])
        if decoded is None or len(decoded) < 11 * 8:
            return None
        decoded = [1 - x for x in decoded]  # invert
        b = _bits_to_bytes(decoded[:11 * 8])
        if len(b) < 11:
            return None
        b = bytes(_reverse8(x) for x in b)
        if b[0] != 0xA5:
            return None
        chk_calc = sum(b[1:10]) & 0xFF
        if chk_calc != b[10]:
            return None
        id_      = (b[4] << 24) | (b[3] << 16) | (b[2] << 8) | b[1]
        bat_low  = (b[5] & 0x02) >> 1
        temp_raw = ((b[8] & 0x0F) << 8) | b[7]
        temp_f   = round(temp_raw * 0.1, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           f"{id_:08x}",
            "battery_ok":   int(not bat_low),
            "temperature_F": temp_f,
        })


__all__ = ["BaldrHCS528ARF"]
