"""@file
    CurrentCost TX, CurrentCost EnviR current sensors.

    Copyright (C) 2015 Emmanuel Navarro <enavarro222@gmail.com>
    CurrentCost EnviR added by Neil Cowburn <git@neilcowburn.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

CurrentCost TX, CurrentCost EnviR current sensors.

@todo Documentation needed.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class CurrentCost(RawDecoder):
    """Current Cost EnviR / Classic energy monitor (FSK_PULSE_PCM NRZ, 4 kbps).

    Preamble classic : 0xCC 0xCC 0xCC 0xCE 0x91 0x5D
    Preamble EnviR   : 0x55 0x55 0x55 0x55 0xA4 0x57
    Data (8 bytes, after Manchester layer decode):
        bytes 0-1: device ID (12-bit)
        bytes 2-3: ch0 power W (15-bit, validity flag at MSB)
        bytes 4-5: ch1 power W
        bytes 6-7: ch2 power W
    Counter variant (byte 0 & 0xF0 == 0x40):
        bytes 4-7: 32-bit impulse counter
        byte 3   : sensor type (2=electric, 3=gas, 4=water)
    No CRC implemented in rtl_433 source.
    """
    name = "CurrentCost"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["CurrentCost"]
