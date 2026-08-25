"""@file
    OpenEnergyMonitor.org emonTx sensor protocol.

    Copyright (C) 2016 Tommy Vestermark
    Copyright (C) 2016 David Woodhouse

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

OpenEnergyMonitor.org emonTx sensor protocol.

This is the JeeLibs RF12 packet format as described at
http://jeelabs.org/2011/06/09/rf12-packet-format-and-design/

The RFM69 chip misses out the zero bit at the end of the 0xAA 0xAA 0xAA preamble;
the receivers only use it to set up the bit timing, and they look for the 0x2D at
the start of the packet. The code looks for a group of 0xD2, and expects the CDA
bits in the header to all be zero.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EmonTX(RawDecoder):
    """OpenEnergyMonitor emonTx energy node (FSK_PULSE_PCM, ~49.2 kbps via RFM69).

    Preamble: 0xAA 0xAA 0xAA then header 0x2D 0xD2 0x00 (inverted: 0xD2 0x2D 0xC0).
    Payload:
        node    : 8-bit node ID
        ct1-ct4 : 16-bit signed current transformer readings (A × raw)
        Vrms    : 16-bit RMS voltage (÷100 V)
        temp1-6 : 16-bit × 0.1°C  (value 3000 = no sensor fitted)
        pulse   : 32-bit pulse counter
    Integrity: CRC-16 (poly 0xA001, init 0xFFFF).
    """
    name = "EmonTX"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["EmonTX"]
