"""Astrostart 2000 - Car Remote.

Copyright (C) 2024 Ethan Halsall

Astrostart 2000 - Car Remote 372.4 MHz.

Manufacturer: Astroflex

Supported Models:
- Astrostart 2000 (FCC ID J5F-TX2000)
- Astrostart 3000 (FCC ID J5F-TX2000)

The transmitter uses a fixed code message. Each button press will always send three messages.

Button operation:
This transmitter has 5 (Astrostart 2000) or 6 (Astrostart 3000) buttons.
One or two buttons at a time can be pressed and held to send a unique code.
Pressing three buttons will result in a code, but is not unique to different button combinations.

The transmitter supports sending two serial numbers. Press and hold a button combination once
to use the primary serial number. The second serial number can be used by pressing the buttons
in the below sequence:
1. Press a button or button combination twice, holding the combinations on the second press.
2. Hold the buttons down until you hear the four beeps / see the led flash slowly four times.

Note: The panic button will always send two messages on the primary serial number, and one
message on the secondary number.

Data layout:

    B X IIII cccc

- B: 8 bit button code
- X: 8 bit inverse of the button code
- I: 32 bit remote id
- c: 4 bit checksum of remote id

Format string:

    BUTTON: bbbbbbbb INVERSE: bbbbbbbb ID: hhhhhhhh CHECKSUM: h
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
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


def _add_nibbles(data: bytes | bytearray, n: int) -> int:
    """Sum both nibbles of the first *n* bytes in *data*."""
    total = 0
    for i in range(min(n, len(data))):
        total += (data[i] >> 4) + (data[i] & 0xF)
    return total


class AstrostartCarRemote(OOKPPMDecoder):
    """Astrostart 2000 Car Remote  372.4 MHz, OOK PPM, 52 bits.

    Frame: button(8) | ~button(8) | id(32) | nibble_cksum(4) | pad(4).
    Integrity: byte 1 must be bitwise inverse of byte 0.
    Checksum: sum of all nibbles in bytes 2-5 equals upper nibble of byte 6.
    """
    name      = "Astrostart 2000 Car Remote"
    short_us  = 326.0
    long_us   = 526.0
    reset_us  = 541.0
    n_bits    = 52
    tolerance = 0.25      # ≈80 µs / 326 µs

    BUTTONS: dict[int, str] = {
        0x01: "Start", 0x02: "Stop",   0x04: "Lock",
        0x08: "Unlock", 0x10: "Trunk", 0x20: "Panic", 0x40: "Aux",
    }

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) != 52:
            return None
        data = _bits_to_bytes(bits)  # 7 bytes

        # Inverse check: byte 0 must be bitwise inverse of byte 1
        if data[0] != ((~data[1]) & 0xFF):
            return None

        button_code = data[0]
        remote_id   = (data[2] << 24) | (data[3] << 16) | (data[4] << 8) | data[5]

        # Nibble checksum: sum of nibbles in bytes 2-5 must equal upper nibble of byte 6
        nibble_sum = _add_nibbles(data[2:6], 4) & 0xF
        expected   = (data[6] >> 4) & 0xF
        if nibble_sum != expected:
            return None

        button_name = self.BUTTONS.get(button_code, f"0x{button_code:02X}")
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"0x{remote_id:08X}",
            "button_code": button_code,
            "button": button_name,
        })


__all__ = ["AstrostartCarRemote"]
