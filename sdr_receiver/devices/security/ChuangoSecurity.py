"""Chuango Security Technology.

Copyright (C) 2015 Tommy Vestermark

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Chuango Security Technology.

Likely based on HS1527 or compatible

Tested devices:
- G5 GSM/SMS/RFID Touch Alarm System (Alarm, Disarm, ...)
- DWC-100 Door sensor (Default: Normal Zone)
- DWC-102 Door sensor (Default: Normal Zone)
- KP-700 Wireless Keypad (Arm, Disarm, Home Mode, Alarm!)
- PIR-900 PIR sensor (Default: Home Mode Zone)
- RC-80 Remote Control (Arm, Disarm, Home Mode, Alarm!)
- SMK-500 Smoke sensor (Default: 24H Zone)
- WI-200 Water sensor (Default: 24H Zone)
- newer DWC-102 additionally generates a cmd=12 signal on door/windows being closed
- Compustar 700R Car Remote
- Compustar 900R Car Remote

Note: simple 24 bit fixed ID protocol (x1527 style) and should be handled by the flex decoder.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


_CHUANGO_CMD: dict[int, str] = {
    0x0: "Test", 0x1: "Disarm", 0x2: "Alarm", 0x3: "Tamper",
    0x4: "Home Mode", 0x5: "On", 0x6: "Home Mode Zone",
    0x7: "Normal Zone", 0x8: "Arm", 0xA: "Single Delay Zone",
    0xB: "24H Zone", 0xC: "Closing", 0xD: "Low Battery",
}


class ChuangoSecurity(OOKPWMDecoder):
    """Chuango OOK security sensor (PIR, door/window, smoke).

    OOK_PULSE_PWM 568/1704 µs, 25 bits, no checksum.
    Bits are transmitted with short=1 / long=0 (inverted relative to our base).
    """

    name      = "Chuango-Security"
    short_us  = 568.0
    long_us   = 1704.0
    reset_us  = 1800.0
    n_bits    = 25
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 25:
            return None
        # MSB of byte 3 (raw bit 24) must be 1 before inversion
        if bits[24] != 1:
            return None
        # Invert bits 0-23 (physical: short=1, long=0)
        b = [x ^ 1 for x in bits[:24]]
        b0 = bits_to_int(b[0:8])
        b1 = bits_to_int(b[8:16])
        b2 = bits_to_int(b[16:24])
        sensor_id = (b0 << 12) | (b1 << 4) | (b2 >> 4)
        if sensor_id == 0:
            return None
        cmd = b2 & 0x0F
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":     sensor_id,
            "cmd":    _CHUANGO_CMD.get(cmd, f"unknown(0x{cmd:X})"),
            "cmd_id": cmd,
        })


__all__ = ["ChuangoSecurity"]
