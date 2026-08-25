"""Cellular Tracking Technologies (CTT) LifeTag/PowerTag/HybridTag.

Copyright (C) 2025 Jonathan Caicedo <jonathan@jcaicedo.com>
Credit to https://github.com/tve for the CTT tag implementation details via their work on RadioJay (https://radiojay.org/) and Motus Test Tags (https://github.com/tve/motus-test-tags).

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Cellular Tracking Technologies (https://celltracktech.com/) LifeTag/PowerTag/HybridTag.

The CTT LifeTag/PowerTag/HybridTag is a lightweight transmitter used for wildlife tracking and research -
most commonly used with the Motus Wildlife Tracking System (https://motus.org/).
The tags transmit a unique identifier (ID) at a fixed bitrate of 25 kbps using Frequency Shift Keying (FSK)
modulation on 434 MHz.

The packet format consists of:

- PREAMBLE: 24 bits of alternating 1/0 (0xAA if byte-aligned) for receiver bit-clock sync
- SYNC:     2 bytes fixed pattern 0xD3, 0x91 marking the packet start
- ID:       20-bit tag ID encoded into 4 bytes (5 bits per byte) using a 32-entry dictionary
- CRC:      1-byte SMBus CRC-8 over the 4 encoded ID bytes

    AA AA AA   D3 91   78 55 4C 33   58
   |--------| |-----| |-----------| |--|
    Preamble   Sync        ID       CRC

- LifeTag: programmed with a standard 5-second beep rate.
- PowerTag: user-defined beep rate.
- HybridTag: transmits a beep every 2-15 seconds.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class CttLifePowerHybrid(RawDecoder):
    """CTT LifeTag/PowerTag/HybridTag  FSK PCM, CRC-8 SMBus."""
    name = "CTT-LifePowerHybrid"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["CttLifePowerHybrid"]
