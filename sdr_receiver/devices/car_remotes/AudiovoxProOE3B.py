"""Audiovox - PRO-OE3B Car Remote.

Copyright (C) 2024 Ethan Halsall

Audiovox - Car Remote.

Manufacturer: Audiovox

Supported Models:
- PRO-OE3B, AVX01BT3CL3 (FCC ID BGAOE3B)
- PRO-OE4B, AVX01BT3CL3 (FCC ID BGAOE3B)

This transmitter uses a fixed code transmitting on 302.9 MHz. The same code is
continuously repeated while button is held down. Multiple buttons can be pressed
to set multiple button flags. Bits are inverted.

Data layout:

    IIII 110b1b1b 1111

where I is 16 bit ID, 1 is always set to 1, 0 is always set to 0,
b is 3 bit flags indicating button(s) pressed.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
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


class AudiovoxProOE3B(OOKPWMDecoder):
    """Audiovox PRO-OE3B Car Remote  303.4 MHz, OOK PWM, 25 bits.

    Bits are inverted before field extraction.  No checksum; integrity is
    inferred from the fixed-pattern structure of byte 2.
    """
    name     = "Audiovox PRO-OE3B Car Remote"
    short_us = 445.0
    long_us  = 895.0
    reset_us = 1790.0
    n_bits   = 25

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) != 25:
            return None

        # Invert all bits (C decoder: bitbuffer_invert)
        bits = [1 - b for b in bits]
        data = _bits_to_bytes(bits)

        # Sanity on byte 2: reject if any 'A' pattern bit is set or all bits set
        if (data[2] & 0xAA) or data[2] == 0x55:
            return None

        remote_id = (data[0] << 8) | data[1]
        if remote_id in (0x0000, 0xFFFF):
            return None

        lock   = bool(bits[17])
        unlock = bool(bits[19])
        option = bool(bits[21])
        trunk  = bool(bits[23])

        buttons = []
        if lock:   buttons.append("Lock")
        if unlock: buttons.append("Unlock")
        if option: buttons.append("Option")
        if trunk:  buttons.append("Trunk")
        if not buttons:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"0x{remote_id:04X}",
            "button": "+".join(buttons),
            "lock": int(lock),
            "unlock": int(unlock),
            "option": int(option),
            "trunk": int(trunk),
        })


__all__ = ["AudiovoxProOE3B"]
