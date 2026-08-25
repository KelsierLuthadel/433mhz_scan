"""@file
    Decoder for Eco-Eye solar PV / grid current monitor.

    Copyright (C) 2026 Benjamin Larsson

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Decoder for Eco-Eye solar PV / grid current monitor.

https://www.eco-eye.com/product-monitor-solar-smartpv

Transmitter unit with two current clamps (grid usage and PV/solar generation)
sending to a paired display every 4 seconds.

The transmission is FSK PCM with 200 us bit width.

Data layout, after the aa2dd4 sync word:

    PPPPPPPPPPPPPPPP UUUUUUUUUUUUUUUU CCCCCCCC

- P: 16 bit PV/solar generation current, centi-amps (0.01 A/count)
- U: 16 bit grid current used, centi-amps (0.01 A/count)
- C: 8 bit checksum

Checksum is a simple byte-add: b0+b1+b2+b3 == b4 (mod 256).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EcoEye(RawDecoder):
    """Eco-Eye solar / smart meter (FSK_PULSE_PCM, 5 kbps).

    Preamble: 0xAA 0x2D 0xD4
    Data (5 bytes after preamble):
        bytes 0-1: PV generation current (×0.01 A)
        bytes 2-3: grid usage current (×0.01 A)
        byte 4   : checksum = sum(bytes 0-3) mod 256
    """
    name = "EcoEye"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["EcoEye"]
