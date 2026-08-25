"""MIC 6SC2 Car Remote  315.1 MHz, OOK Manchester, 72-88 bits.

Preamble: bytes 0-1 must be 0x55, 0x54.
Integrity: XOR of bytes 2-10 must equal zero.
Button nibble (upper nibble of byte 6): 0x1=Unlock, 0x2=Lock, 0x4=Trunk, 0x8=Panic.
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


class Mic6SC2CarRemote(ManchesterDecoder):
    """MIC 6SC2 Car Remote  315.1 MHz, OOK Manchester, 72-88 bits.

    Preamble: bytes 0-1 must be 0x55, 0x54.
    Integrity: XOR of bytes 2-10 must equal zero.
    Button nibble (upper nibble of byte 6): 0x1=Unlock, 0x2=Lock, 0x4=Trunk, 0x8=Panic.
    """
    name     = "MIC 6SC2 Car Remote"
    chip_us  = 250.0
    reset_us = 10000.0
    n_bits   = 88

    BUTTONS: dict[int, str] = {
        0x1: "Unlock", 0x2: "Lock", 0x4: "Trunk", 0x8: "Panic",
    }

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 72 or len(bits) > 88:
            return None
        # Pad to 88 bits so we always have 11 bytes
        bits = list(bits) + [0] * (88 - len(bits))
        data = _bits_to_bytes(bits)  # 11 bytes

        # Preamble
        if data[0] != 0x55 or data[1] != 0x54:
            return None

        # XOR checksum over bytes 2-10 must be zero
        xor_val = 0
        for b in data[2:11]:
            xor_val ^= b
        if xor_val != 0:
            return None

        button_nibble = (data[6] >> 4) & 0xF
        sequence      = (data[7] << 8) | data[8]
        encrypted     = bits_to_int(bits[16:48])

        button_name = self.BUTTONS.get(button_nibble, f"0x{button_nibble:X}")
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"0x{encrypted:08X}",
            "button_code": button_nibble,
            "button": button_name,
            "sequence": sequence,
        })


__all__ = ["Mic6SC2CarRemote"]
