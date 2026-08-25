"""Celsia CZC1 Thermostat.

Copyright (C) 2023 Liban Hannan <liban.p@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Celsia CZC1 Thermostat.

A PID thermostat compatible with various manufacturers' heaters.

demod: OOK_PCM
short: 1220
long: 1220
reset: 4880

A packet starts with a preamble of {40}cccccccccccccccccccc, followed by a sync
of {32}55555555 signalling the start of the data symbols. The packet is
terminated with {8}f0.  Each symbol is 4 'raw' bits long: 0101(5) = 0, 1010(a)
= 1. Command packets have 5 bytes of data, pairing packets have 4.

Data layout:

Command packet (5 bytes)

- ID:   {16} ID
- Type: {8}  type
- Heat: {8}  heating level 0-255 (bit reflected unsigned integer)
- CRC:  {8}  CRC-8, poly 0x31, init 0xd7

Pairing packet (4 bytes)

- ID:   {16} ID
- Type: {8}  type
- CRC:  {8}  CRC-8, poly 0x31, init 0xd7
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class CelsiaCzc1(RawDecoder):
    """Celsia CZC1 Thermostat  OOK PCM with 4b→2b symbol encoding."""
    name = "Celsia-CZC1"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["CelsiaCzc1"]
