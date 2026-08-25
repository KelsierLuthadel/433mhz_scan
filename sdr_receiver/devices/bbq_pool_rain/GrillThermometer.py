"""@file
    Remote Grill Thermometer temperature sensor.

    Copyright (C) 2023 Ethan Halsall

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Remote Grill Thermometer -- Generic wireless thermometer with probe.

This is a meat thermometer with no brand / model identification except the FCC ID.

Manufacturer: Yangzhou Fupond Electronic Technology Corp., Ltd
Supported Models: RF-T0912 (FCC ID TXRFPT0912)

9 - 415 F, frequency 434.052 MHz

10 repetitions of the same 24 bit payload:

    AAAAAAAA AAAAAAAA BBBBBBBB

- A: 16 bit temperature in Fahrenheit. Big Endian.
- B: Checksum of A
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from .._helpers import _bits_to_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GrillThermometer(OOKPWMDecoder):
    """RF-T0912 Grill Thermometer (Yangzhou Fupond, FCC TXRFPT0912).

    OOK_PULSE_PWM, inverted, 24 bits per row, 10 repetitions.
    Bytes [0:2] = temperature_F (signed 16-bit BE), [2] = sum checksum.
    """

    name     = "RF-T0912"
    short_us = 252.0
    long_us  = 736.0
    reset_us = 8068.0
    n_bits   = 24

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Signal is inverted relative to standard PWM polarity.
        bits = [1 - b for b in bits]
        b = _bits_to_bytes(bits)
        if len(b) < 3:
            return None
        checksum = (b[0] + b[1]) & 0xFF
        if checksum != b[2] or checksum == 0:
            return None
        temp_f = (b[0] << 8) | b[1]
        if temp_f >= 0x8000:
            temp_f -= 0x10000  # sign-extend 16-bit
        overload = (temp_f == -1029)
        fields: dict = {"model": self.name, "overload": int(overload)}
        if not overload:
            fields["temperature_F"] = float(temp_f)
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["GrillThermometer"]
