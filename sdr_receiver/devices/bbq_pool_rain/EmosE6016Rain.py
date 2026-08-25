"""@file
    EMOS E6016 rain gauge.

    Copyright (C) 2022 Dirk Utke-Woehlke <kardinal26@mail.de>
    Copyright (C) 2022 Stefan Tomko <stefan.tomko@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

EMOS E6016 rain gauge.

- Manufacturer: EMOS
- Transmit Interval: every 85s
- Frequency: 433.92 MHz
- Modulation: OOK PWM, INVERTED

Data Layout:

    PP PP PP II BU UU UR RR XX

- P: (24 bit) preamble
- I: (8 bit) ID
- B: (2 bit) battery indication
- U: (18 bit) Unknown
- R: (12 bit) Rain
- X: (8 bit) checksum
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from .._helpers import _bits_to_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EmosE6016Rain(OOKPWMDecoder):
    """EMOS E6016 Rain Gauge.

    OOK_PULSE_PWM (inverted), 72–73 bits.
    Preamble (pre-inversion): 0x55 0x5A 0x75.
    After inversion: ID(8) BAT(2) UNK(18) RAIN(12) CHECKSUM(8).
    Checksum = sum of bytes 0-7 & 0xFF.
    """

    name     = "EMOS-E6016R"
    short_us = 300.0
    long_us  = 800.0
    reset_us = 2500.0
    n_bits   = 72

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 72:
            return None
        # Check preamble in NON-inverted bits (raw as decoded by OOK PWM)
        b_raw = _bits_to_bytes(bits[:24])
        if len(b_raw) < 3:
            return None
        if b_raw[0] != 0x55 or b_raw[1] != 0x5A or b_raw[2] != 0x75:
            return None
        # Now invert all bits
        bits_inv = [1 - x for x in bits[:72]]
        b = _bits_to_bytes(bits_inv)
        if len(b) < 9:
            return None
        chk_calc = sum(b[:8]) & 0xFF
        if chk_calc != b[8]:
            return None
        id_      = b[3]
        battery  = (b[4] >> 6)
        rain_raw = ((b[6] & 0x0F) << 8) | b[7]
        rain_mm  = round(rain_raw * 0.7, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         id_,
            "battery_ok": int(battery > 0),
            "rain_mm":    rain_mm,
        })


__all__ = ["EmosE6016Rain"]
