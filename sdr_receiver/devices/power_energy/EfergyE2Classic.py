"""@file
    Efergy e2 classic (electricity meter).

    Copyright (C) 2015 Robert Högberg <robert.hogberg@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Efergy e2 classic (electricity meter).

This electricity meter periodically reports current power consumption
on frequency ~433.55 MHz. The data that is transmitted consists of 8 bytes:

- Byte 1: Start bits (00)
- Byte 2-3: Device id
- Byte 4: Learn mode, sending interval and battery status
- Byte 5-7: Current power consumption
  -  Byte 5: Integer value (High byte)
  -  Byte 6: integer value (Low byte)
  -  Byte 7: exponent (values between -3? and 4?)
- Byte 8: Checksum

Power calculations come from Nathaniel Elijah's program EfergyRPI_001.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EfergyE2Classic(RawDecoder):
    """Efergy e2 Classic energy monitor (FSK_PULSE_PWM, ~15.6 kbps).

    Frame (8 bytes, 64-65 bits):
        byte 0   : start bits
        bytes 1-2: device ID (16-bit)
        byte 3   : learn (bit 7), interval (bits 5-4), battery (bit 6)
        bytes 4-6: power  16-bit mantissa + 8-bit exponent
                   current_A = mantissa × 2^exponent
        byte 7   : checksum = sum(bytes 0-6) mod 256
    """
    name = "Efergy-E2-Classic"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["EfergyE2Classic"]
