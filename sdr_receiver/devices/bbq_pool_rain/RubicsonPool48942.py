"""@file
    Rubicson pool thermometer 48942 decoder.

    Copyright (C) 2022 Robert Högberg

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Rubicson pool thermometer 48942 decoder.

The device uses OOK and fixed period PWM.
- 0 is encoded as 240 us pulse and 480 us gap,
- 1 is encoded as 480 us pulse and 240 us gap.

A transmission consists of an initial preamble followed by sync pulses and the data.
Sync pulses and data are sent twice.

Data format:

    CCCCRRRR RRRRRR10 BTTTTTTT TTTT0000 XXXXXXXX 0

- C: channel - offset by 1; 0000 means channel 1 (configurable 1-8)
- R: random power on id
- B: low battery indicator
- T: temperature - offset by 1024 and scaled by 10
- X: CRC
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from .._helpers import _bits_to_bytes
from ...dsp import crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class RubicsonPool48942(OOKPWMDecoder):
    """Rubicson Pool Thermometer 48942.

    OOK_PULSE_PWM (inverted), 41 bits.
    Layout (after inversion): CCCC RRRR RRRR RR10 B TTTTTTT TTTT 0000 XXXXXXXX 0
    CRC-8 poly=0x31 over bytes 0-3.
    """

    name     = "Rubicson-48942"
    short_us = 280.0
    long_us  = 480.0
    reset_us = 6000.0
    n_bits   = 41

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 41:
            return None
        # Signal is inverted
        bits = [1 - b for b in bits]
        b = _bits_to_bytes(bits[:40])
        if len(b) < 5:
            return None
        # Validate static bits: low nibble of b[3] == 0, b[5](trailing bit) == 0
        if b[3] & 0x0F:
            return None
        if b[0] == 0 and b[2] == 0 and b[4] == 0:
            return None
        if crc8(b[:4], 0x31, 0x00) != b[4]:
            return None
        channel     = (b[0] >> 4) + 1
        random_id   = ((b[0] & 0x0F) << 6) | ((b[1] & 0xFC) >> 2)
        battery_low = b[2] >> 7
        temp_raw    = ((b[2] & 0x7F) << 4) | (b[3] >> 4)
        temp_c      = round((temp_raw - 1024) * 0.1, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "channel":    channel,
            "id":         random_id,
            "battery_ok": int(not battery_low),
            "temperature_C": temp_c,
        })


__all__ = ["RubicsonPool48942"]
