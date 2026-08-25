"""GM - Car Remote.

Copyright (C) 2024 Ethan Halsall

General Motors - Car Remote (315 MHz).

Manufacturer: General Motors

Supported Models:
- ABO1502T

The transmitter uses a rolling code message with an unencrypted sequence number.

Button operation:
This transmitter has 2 to 4 buttons which can be pressed once to transmit a single message.
Pressing both lock and unlock appears to send a fixed code, possibly a PRNG seed or secret key
for the rolling code.

Data layout:

    PP xxxx cccc IIIIIIII SSSSSS EEEEEE CC

- P: 8 bit unknown, possibly part of the ID
- c: 4 bit checksum of button code
- b: 4 bit button code
- I: 32 bit ID
- S: 24 bit sequence
- E: 24 bit encrypted
- C: 8 bit checksum of entire payload

Format string:

    UNKNOWN: bbbbbbbb BUTTON_CHECKSUM: bbbb BUTTON: bbbb ID: hhhhhhhh SEQUENCE: hhhhhh ENCRYPTED: hhhhhh CHECKSUM: hh
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


class GMCarRemote(OOKPPMDecoder):
    """GM ABO1502T Car Remote  314.9 MHz, OOK PPM, 113 bits.

    Frame: wake(8) | btn_cksum(4) | btn_code(3) | pad(1) | id(32) |
           seq(24) | encrypted(24) | full_cksum(8).
    Button nibble-sum of byte 1 must be divisible by 16; arithmetic sum of
    bytes 1-13 must be divisible by 256.
    """
    name     = "GM ABO1502T Car Remote"
    short_us = 300.0
    long_us  = 500.0
    reset_us = 20000.0
    n_bits   = 113

    BUTTONS: dict[int, str] = {
        0: "None", 1: "Lock", 2: "Unlock", 3: "Trunk",
        4: "Remote Start", 5: "Panic",
    }

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 113:
            return None
        # Payload is at the end of whatever was received
        bits = list(bits[-113:])
        data = _bits_to_bytes(bits)  # 15 bytes (113 bits)

        # Byte 0 must be wake byte 0xFF
        if data[0] != 0xFF:
            return None

        # Button nibble check: both nibbles of byte 1 must sum to 0 mod 16
        if _add_nibbles(data[1:2], 1) & 0xF:
            return None

        # Full checksum: sum of bytes 1-13 must be 0 mod 256
        if sum(data[1:14]) & 0xFF:
            return None

        button_code = (data[1] >> 1) & 0x7
        device_id   = bits_to_int(bits[16:48])
        sequence    = bits_to_int(bits[48:72])
        encrypted   = bits_to_int(bits[72:96])

        button_name = self.BUTTONS.get(button_code, f"0x{button_code:X}")
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"0x{device_id:08X}",
            "button_code": button_code,
            "button": button_name,
            "sequence": sequence,
            "encrypted": f"0x{encrypted:06X}",
        })


__all__ = ["GMCarRemote"]
