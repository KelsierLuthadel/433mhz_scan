"""Funkbus / Instafunk.

Copyright (C) 2021 Markus Sattler

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Funkbus / Instafunk.

Used by Berker, Gira, Jung and may more
developed by Insta GmbH.

- Frequency: 433.42MHz
- Preamble: 4000us
- Short: 500us
- Long: 1000us
- Encoding: Differential Manchester Biphase-Mark (BP-M)
- Mic: parity + lfsr with 8bit mask 0x8C shifted left by 2 bit
- Bits: 48
- Endian: LSB

Data layout:

    TS II II IF FA AX

- T: 4 bit type, there are multiple types
- S: 4 bit subtype
- I: 20 bit serial number
- F: 2 bit r1, unknown
- F: 1 bit bat, 1 == battery low
- F: 2 bit r2, unknown
- F: 3 bit command, button on the remote
- A: 2 bit group, remote channel group 0-2 (A-C) are switches, 3 == light scene
- A: 1 bit r3, unknown
- A: 2 bit action, STOP, OFF, ON, SCENE
- A: 1 bit repeat, 1 == not first send of packet
- A: 1 bit longpress, longpress of button for (dim up/down, scene learning)
- A: 1 bit parity, parity over all bits before
- X: 4 bit check, LFSR with 8 bit mask 0x8C shifted left by 2 each bit

Some details can be found by searching "instafunk RX/TX-Modul pdf".
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Funkbus(RawDecoder):
    """Funkbus / Instafunk 433 MHz building-automation remote.

    OOK_PULSE_DMC (Differential Manchester), chip=500 µs, long=1000 µs, reset=2000 µs.
    48 bits LSB-first: type[4] | subtype[4] | serial[20] | battery[1] | cmd[3] |
    group[2] | action[2] | flags[2] | parity[1] | LFSR_chk[4].
    Only type=0x4, subtype=0x3 (remote) packets are decoded.
    Stub: Differential Manchester decoding not yet implemented.
    """
    name = "Funkbus"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires differential Manchester decoding


__all__ = ["Funkbus"]
