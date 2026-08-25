"""Amazon Basics Meat Thermometer

Copyright (C) 2021 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Amazon Basics Meat Thermometer

Manchester encoded PCM signal.

[00] {48} e4 00 a3 01 40 ff

II 00 UU TT T0 FF

I - power on random id
0 - zeros
U - Unknown
T - bcd coded temperature
F - ones
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AbmtDecoder(RawDecoder):
    """Amazon Basics Meat Thermometer  OOK PCM with Manchester + BCD temp."""
    name = "ABMT"

    def decode(self, pulses, freq_hz):
        # OOK_PULSE_PCM chip=550 µs but requires Manchester post-processing
        # and a 0x55AAAA sync search  not feasible in raw OOK pipeline.
        return None


__all__ = ["AbmtDecoder"]
