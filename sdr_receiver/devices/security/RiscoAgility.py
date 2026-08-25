"""Risco 2 way Agility protocol.

Copyright (C) 2024 Bruno OCTAU (ProfBoc75)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Risco 2 way Agility protocol.

Manufacturer :
- Risco Ltd.

Reference:
- Risco PIR RWX95PA Agility sensor,

FCC extract:
- The module is a transceiver which consist of a small PCB with an integral helical antenna,
which operates in the frequency of 433.92MHz Modulation is On-Off Keying using Manchester code with max bit rate of 2400Bps.
This module is installed only in RISCO 2-way wireless units, and it's behavior is determined by the host unit, as tested by ITL.
- Being bi-directional enables the detectors to receive an acknowledgment from the panel for every transmission.

S.a. issue #3062

Data Layout:
- 2 types of message have been identified.
- 16 bytes
- or 33 bytes

Preamble/Syncword  .... : 0x555a

Short 16 bytes message:
                   0  8  16 24 34 40 48 56 64 72 80 88 96104112120
    Byte Position   0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
    Sample         ff 60 01 e1 9c b6 01 74 fe 28 0c 60 60 00 50 be
                   AA AA BB BC DD DD EE EE EE FF FF GG HI JJ ZZ ZZ

- AA:{16} flag 1, fixed 0xFF60
- BB:{12} flag 2, fixed 0x01E
- C: {4}  0 or 1 flag 3
- D: {16} Counter, 8 bits reversed and reflected binary coded, one bit change between message, each byte increases to maximum then decreases.
- EE:{24} Possible ID, not yet decoded from Wxxxxxxxxxxx number on the QR sticker.
- FF:{16} Fixed 0x280c value
- GG:{8}  flag 4, 0x60 from PIR sensor, 0xA0 from other type frame
- H: {4}  Alarm state, 0x6 (0x4 Gray decoded) = Tampered, 0xA (0x6) = Tampered_motion, 0xC (0x2) = Motion, 0x0 = Clear, not detection.
- I: {4}  0x0 = Normal, 0x3 (0x8) = Low Bat ?
- J: {4}  0 or 1
- ZZ:{16} CRC-16, poly 0x8005, init 0x8181
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _gray_decode(n: int) -> int:
    mask = n >> 1
    while mask:
        n ^= mask
        mask >>= 1
    return n


class RiscoAgility(RawDecoder):
    """Risco 2-Way Agility PIR sensor (OOK_PULSE_PCM + differential Manchester).

    16-byte message, preamble 0x555A, Gray-coded fields, CRC-16(0x8005, 0x8181).
    Requires differential Manchester decoding.
    """

    name = "Risco-Agility"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["RiscoAgility"]
