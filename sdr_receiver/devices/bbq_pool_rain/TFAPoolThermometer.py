"""@file
    TFA pool temperature sensor.

    Copyright (C) 2015 Alexandre Coffignal

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

TFA pool temperature sensor.

Tested with TFA-Pool-thermometer 30.3160.

Sends 10 24 bits frames.

Data layout:

    CCCCIIII IIIITTTT TTTTTTTT DDBF

- C: checksum, sum of nibbles - 1
- I: device id (changing only after reset)
- T: temperature
- D: channel number
- B: battery status
- F: first transmission
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from .._helpers import _bits_to_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFAPoolThermometer(OOKPPMDecoder):
    """TFA Pool Temperature Sensor 30.3160.

    OOK_PULSE_PPM, 28 bits.
    Layout: CCCC IIII IIII TTTT TTTT TTTT DD BF
    Checksum = sum of data nibbles - 1 (low nibble of byte 0).
    """

    name     = "TFA-Pool"
    short_us = 2000.0
    long_us  = 4600.0
    reset_us = 10000.0
    n_bits   = 28

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 28:
            return None
        b = _bits_to_bytes(bits[:28])
        if len(b) < 4:
            return None
        chk_rx = (b[0] & 0xF0) >> 4
        chk = ((b[0] & 0x0F) + (b[1] >> 4) + (b[1] & 0x0F) +
               (b[2] >> 4) + (b[2] & 0x0F) + (b[3] >> 4) - 1) & 0x0F
        if chk_rx != chk:
            return None
        device  = ((b[0] & 0x0F) << 4) | ((b[1] & 0xF0) >> 4)
        t_raw   = ((b[1] & 0x0F) << 8) | b[2]
        if t_raw > 2048:
            t_raw -= 4096
        temp_c  = round(t_raw * 0.1, 1)
        channel = (b[3] & 0xC0) >> 6
        battery = (b[3] & 0x20) >> 5
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         device,
            "channel":    channel,
            "battery_ok": battery,
            "temperature_C": temp_c,
        })


__all__ = ["TFAPoolThermometer"]
