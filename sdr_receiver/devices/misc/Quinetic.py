"""Quinetic Switches and Sensors.

Copyright (C) 2024 Nick Parrott

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Quinetic Switches and Sensors.

Frame Layout:

    ...PPPP SS IISCC

- P: 48-bits+ of Preamble
- S: 16-bits of Sync-Word (0xA4, 0x23)
- I: 16-bits of Device ID
- S: 8-bits of Device Action
- C: 16-bits of In-Packet Checksum (CRC-16 AUG-CCITT)

Signal Summary:

- Frequency: 433.3 Mhz, +/- 50Khz
- Nominal pulse width: 10us
- Modulation: FSK_PCM
- Checksum: CRC-16/AUG-CCITT

Device Characteristics:

- A switch emits 3-4 pulses when button is pressed.
- A switch emits 3-4 pulses when button is released.
- Device ID is preserved as 16-bit Hex.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Quinetic(RawDecoder):
    """Quinetic switch  FSK PCM (requires 433.4 MHz, 1024 kS/s)."""
    name = "Quinetic"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["Quinetic"]
