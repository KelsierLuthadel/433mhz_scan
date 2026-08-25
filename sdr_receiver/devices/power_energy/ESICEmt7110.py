"""@file
    ESIC EMT7110 power meter (for EMR7370 receiver).

    Copyright (C) 2019 Christian W. Zuckschwerdt <zany@triq.net>
    Samples and analysis by Petter Reinholdtsen <pere@hungry.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

ESIC EMT7110 power meter (for EMR7370 receiver).

- Center Frequency: 868.28 MHz
- Modulation: FSK
- Deviation: +/- 90 kHz
- Datarate: 9.579 kbit/s
- Preamble: 0xAAAA
- Sync-Word: 0x2DD4

A transmission is two packets, 14 ms apart.

Data Layout:

    II II II II FP PP CC CC VV UE EE XX

- I: (32 bit) Sender ID
- F: (2 bit) Bit6 = power connected, Bit7 = Pairing mode
- P: (14 bit) Power in 0.5 W
- C: (16 bit) Current in mA
- V: (8 bit) Voltage in V, Scaled by 2, Offset by 128 V
- U: (2 bit) unknown
- E: (14 bit) Energy usage total, in 10 Wh (0.01 kWh)
- X: (8 bit) Checksum (sum of all 11 data bytes plus CHK is 0 mod 256)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ESICEmt7110(RawDecoder):
    """ESIC EMT7110 wireless power meter plug (FSK_PULSE_PCM, ~9.6 kbps).

    Preamble: 0xAA 0x2D 0xD4
    Frame (12 bytes after preamble):
        bytes 0-3 : sender ID (32-bit)
        byte 4    : connected (bit 7), pairing (bit 6), power high (bits 5-0)
        byte 5    : power low  → power_W = 14-bit value × 0.5
        bytes 6-7 : current (16-bit mA)
        byte 8    : voltage  → voltage_V = byte × 0.5 + 128
        bytes 9-10: energy → energy_kWh = 14-bit value × 0.01
        byte 11   : checksum (sum of all 12 bytes mod 256 == 0)
    """
    name = "ESIC-EMT7110"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["ESICEmt7110"]
