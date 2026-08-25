"""Norgo Energy NGE101 decoder.

Copyright (C) 2019 jamaron

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Norgo Energy NGE101 decoder.

The code is based on info and code from Jesper Hansen's pages (used with
his permission):
http://blog.bitheap.net/p/this-is-overview-of-data-norge-nge101.html

The signal is FM encoded with clock cycle around x us, using
inverted OOK_PULSE_DMC modulation, i.e.
- No level shift within the clock cycle translates to a logic 1
- One level shift within the clock cycle translates to a logic 0
Each clock cycle begins with a level shift

Each transmission is either 55 or 71 bits long.

Data is transmitted in pure binary values, LSbit first.

Energy meter transmits pulse duration and pulse count as separate messages.
Transmissions also includes channel code and device ID. The sensor transmits
every 43 seconds 2 packets (55 bit packet twice or 71 bit packet together
with 55 bit packet).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Norgo(RawDecoder):
    """Norgo NGE101 energy pulse counter.

    OOK_PULSE_DMC (Differential Manchester), chip=486 µs, long=972 µs, reset=2100 µs.
    Two frame types: 55-bit (type 0, impulse gap) and 71-bit (type 1, impulse count).
    Sync byte: 0xFA (inverted).  XOR/LFSR checksum over each frame.
    Stub: Differential Manchester decoding not yet implemented in OOK pipeline.
    """
    name = "Norgo-NGE101"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires differential Manchester decoding


__all__ = ["Norgo"]
