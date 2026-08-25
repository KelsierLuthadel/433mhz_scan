"""@file
    Efergy IR Optical energy consumption meter.

    Copyright (C) 2016 Adrian Stevenson <adrian_stevenson2002@yahoo.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Efergy IR Optical energy consumption meter.

The data that is transmitted consists of 8 bytes:
- Byte 0-2: Start bits (0000), then static data (probably device id)
- Byte 3: seconds (64: 30s - red led; 80: 60s - orange led; 96: 90s - green led)
- Byte 4-7: all zeros
- Byte 8: Pulse Count
- Byte 9: sample frequency (15 seconds)
- Byte 10-11: bytes 0-9 crc16 xmodem XOR with FF

Transmitter can operate in 3 modes (signaled in bytes[3]):
- red led: information is sent every 30s
- orange led: information is sent every 60s
- green led: information is sent every 90s
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EfergyOptical(RawDecoder):
    """Efergy optical meter adapter (FSK_PULSE_PWM, ~15.6 kbps).

    Frame (12 bytes, 96-100 bits):
        bytes 0-2 : device ID
        byte 3    : transmission interval flag
        bytes 4-7 : padding zeros
        byte 8    : pulse count
        byte 9    : sample frequency
        bytes 10-11: CRC-16/XMODEM (poly 0x1021, init 0x0000)
    Output: id, impulses_per_kWh, pulse_count, energy_kWh.
    """
    name = "Efergy-Optical"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["EfergyOptical"]
