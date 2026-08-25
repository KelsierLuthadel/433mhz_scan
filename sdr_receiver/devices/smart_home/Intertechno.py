"""Intertechno remotes.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Intertechno remotes.

Intertechno remote labeled ITT-1500 that came with 3x ITR-1500 remote outlets. The set is labeled IT-1500.
The PPM consists of a 220us high followed by 340us or 1400us of gap.

There is another type of remotes that have an ID prefix of 0x56 and slightly shorter timing.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Intertechno(OOKPPMDecoder):
    """Intertechno 433 MHz mains socket remote.

    OOK_PULSE_PPM, short=330 µs, long=1400 µs, reset=10000 µs.
    64+ bits; byte 0 == 0x00, byte 1 in {0x56, 0x69}.
    Fields: id (bytes 0-4 hex), command (b[6]&7), slave (b[7]&0xF),
    master ((b[7]>>4)&0xF).  No checksum.
    """
    name     = "Intertechno"
    short_us = 330.0
    long_us  = 1400.0
    reset_us = 10000.0
    n_bits   = 64

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 64:
            return None
        b = [bits_to_int(bits[i : i + 8]) for i in range(0, 64, 8)]
        if b[0] != 0x00:
            return None
        if b[1] not in (0x56, 0x69):
            return None
        device_id = f"{b[0]:02x}{b[1]:02x}{b[2]:02x}{b[3]:02x}{b[4]:02x}"
        command   = b[6] & 0x07
        slave     = b[7] & 0x0F
        master    = (b[7] >> 4) & 0x0F
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":      device_id,
            "command": command,
            "slave":   slave,
            "master":  master,
        })


__all__ = ["Intertechno"]
