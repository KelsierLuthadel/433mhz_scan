"""Siemens 5WY72XX - Car Remote.

Copyright (C) 2024 Ethan Halsall

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Siemens 5WY72XX - Car Remote (315 MHz).

Manufacturer:
- Siemens

Supported Models:
- 5WY72XX, (FCC ID M3N5WY72XX) (OEM for DaimlerChrysler SKREEK CS and RS vehicle platforms.)

Data structure:

The transmitter uses a rolling code message with an unencrypted sequence number.

Data layout (little endian):

    PPPP IIIIIIII bbbbbbbb SSSS EEEEEEEE CC

- P: 16 bit preamble (not included in XOR checksum)
- I: 32 bit ID
- b: 8 bit button code
- S: 16 bit sequence
- E: 32 bit encrypted
- C: 8 bit XOR of entire payload, except preamble
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Siemens5wy72xx(ManchesterDecoder):
    """Siemens 5WY72XX Car Remote (315.1 MHz)."""
    name     = "Siemens-5WY72xx"
    chip_us  = 220.0
    reset_us = 10000.0
    n_bits   = 128

    _BUTTONS = {
        0x01: "Lock", 0x02: "Unlock", 0x04: "Trunk",
        0x08: "Panic", 0x10: "Left Door", 0x20: "Right Door",
    }

    def _parse(self, bits, freq_hz):
        if len(bits) < 113:
            return None
        # Search for 16-bit preamble 0x6001
        start = -1
        for i in range(len(bits) - 16):
            if bits_to_int(bits[i:i + 16]) == 0x6001:
                start = i + 16
                break
        if start < 0 or start + 96 > len(bits):
            return None
        b = [bits_to_int(bits[start + i:start + i + 8]) for i in range(0, 96, 8)]
        # XOR checksum across all 12 bytes must be 0
        xor = 0
        for v in b:
            xor ^= v
        if xor != 0:
            return None
        if all(v == 0 for v in b) or all(v == 0xFF for v in b):
            return None
        device_id   = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
        button_code = b[4]
        seq_num     = (b[5] << 8) | b[6]
        btn_name    = self._BUTTONS.get(button_code, f"0x{button_code:02X}")
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":       f"{device_id:08X}",
            "button":   btn_name,
            "sequence": seq_num,
            "mic":      "CHECKSUM",
        })


__all__ = ["Siemens5wy72xx"]
