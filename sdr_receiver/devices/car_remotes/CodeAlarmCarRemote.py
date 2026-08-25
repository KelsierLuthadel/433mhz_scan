"""Code Alarm - FRDPC2002 Car Remote.

Copyright (C) 2024 Ethan Halsall

Code Alarm - Car Remote.

Manufacturer: Code Alarm

Supported Models:
- FRDPC2002, GOH-FRDPC2002

This transmitter uses a rolling code. The same code is continuously repeated while
button is held down. Multiple buttons can be pressed to set multiple button flags.

Data layout:

    PPPP uuuu bbbb IIIIIIII uuuu

- P: 32 bit Preamble, all 0x00
- u: 4 bit unknown
- b: 4 bit button flags
- I: 24 bit ID (This is 32 bits raw, and each byte is XOR'd to form a 24 bit ID)
- u: 4 bit unknown

Format string:

    PREAMBLE: hhhh UNKNOWN: bbbb BUTTON: bbbb ID: hhhhhhhh bbbbbbbb
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _bits_to_bytes(bits: list[int]) -> bytearray:
    """Pack a list of bits (MSB-first) into a bytearray, zero-padding the last byte."""
    n = (len(bits) + 7) // 8
    result = bytearray(n)
    for i, b in enumerate(bits):
        if b:
            result[i >> 3] |= 0x80 >> (i & 7)
    return result


class CodeAlarmCarRemote(ManchesterDecoder):
    """Code Alarm FRDPC2002 Car Remote  OOK Manchester, 60 bits.

    Preamble: bytes 0-1 must be 0x00.
    ID derived by XOR-chaining four rolling-code bytes.
    """
    name     = "Code Alarm FRDPC2002 Car Remote"
    chip_us  = 550.0
    reset_us = 1600.0
    n_bits   = 60

    BUTTONS: dict[int, str] = {0x1: "Lock", 0x2: "Unlock", 0x4: "Trunk", 0x8: "Panic"}

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 60:
            return None
        bits = bits[:60]
        data = _bits_to_bytes(bits)  # 8 bytes

        # Preamble: first two bytes must be 0x00
        if data[0] != 0x00 or data[1] != 0x00:
            return None

        if sum(data) == 0:
            return None

        # Byte 2: [7:4] = unknown nibble, [3:0] = button flags
        button_flags = data[2] & 0xF

        # Rolling code: bytes 3-6 (4 bytes)
        code = data[3:7]

        # ID: XOR chain of consecutive code bytes
        remote_id = (
            ((code[0] ^ code[1]) << 16) |
            ((code[1] ^ code[2]) << 8)  |
            (code[2] ^ code[3])
        )

        rolling_code = (code[0] << 16) | (code[1] << 8) | code[2]
        buttons = [name for bit, name in self.BUTTONS.items() if button_flags & bit]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"0x{remote_id:06X}",
            "button_flags": button_flags,
            "button": "+".join(buttons) if buttons else "None",
            "rolling_code": f"0x{rolling_code:06X}",
        })


__all__ = ["CodeAlarmCarRemote"]
