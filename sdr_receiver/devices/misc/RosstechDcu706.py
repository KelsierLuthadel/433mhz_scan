"""Rosstech Digital Control Unit DCU-706/Sundance.

Copyright (C) 2023 suaveolent

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Rosstech Digital Control Unit DCU-706/Sundance/Jacuzzi.

Supported Models:
Sundance DCU-6560-131, SD-880 Series, PN 6560-131
Jacuzzi DCU-2560-131, Jac-J300/J400 and SD-780 series, PN 6560-132/2560-131

Data coding:

UART 8o1: 11 bits/byte: 1 start bit (1), odd parity, 1 stop bit (0).

Data layout:

    SS IIII TT CC

- S: 8 bit sync byte and type of transmission
- I: 16 bit ID
- T: 8 bit temp packet in degrees F
- C: 8 bit Checksum: Count 1s for each bit of each element
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class RosstechDcu706(RawDecoder):
    """Rosstech DCU-706 Spa/Hot-tub Controller  OOK PCM with UART 8o1 framing."""
    name = "Rosstech-DCU706"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["RosstechDcu706"]
