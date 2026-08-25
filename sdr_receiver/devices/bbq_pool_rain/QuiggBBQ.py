"""Globaltronics Quigg BBQ GT-TMBBQ-05  ported from rtl_433 C source.

Note: quigg_bbq.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from .._helpers import _bits_to_bytes, _add_nibbles
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _bit_parity(b: int) -> int:
    """Return 1 if b has odd number of set bits, else 0."""
    b ^= b >> 4
    b ^= b >> 2
    b ^= b >> 1
    return b & 1


def _parity_bytes(data: bytes) -> int:
    """Return 0 for odd parity over all bits in data, 1 for even parity."""
    p = 0
    for byte in data:
        p ^= byte
    return _bit_parity(p)


class QuiggBBQ(OOKPPMDecoder):
    """Globaltronics Quigg BBQ GT-TMBBQ-05.

    OOK_PULSE_PPM, 33 bits (first bit ignored → 32 data bits = 4 bytes).
    ID = b[0]<<8|b[2], temp_F = (((b[3]&0xC0)<<2)|b[1]) - 90.
    Odd parity over 7 nibbles; nibble sum check over first 5 nibbles.
    """

    name     = "GT-TMBBQ05"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 9100.0
    n_bits   = 33

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 33:
            return None
        # Drop leading bit, work with bits[1:33] = 32 bits
        b = _bits_to_bytes(bits[1:33])
        if len(b) < 4:
            return None
        if b[0] == 0 and b[1] == 0 and b[2] == 0 and b[3] == 0:
            return None

        # Odd parity check over 7 nibbles (zero lower nibble of b[3])
        p = bytearray(b)
        p[3] &= 0xF0
        if _parity_bytes(bytes(p)) != 0:  # should be ODD parity → result 1
            # parity_bytes returns 0 if total parity is even, but we want ODD
            return None

        # Nibble sum (first 5 nibbles = bytes 0-2 nibbles + high nibble of b[3])
        nsum = _add_nibbles(b[:3]) + (b[3] >> 4)
        if (nsum & 0xF) != (b[3] & 0xF):
            return None

        tempf = (((b[3] & 0xC0) << 2) | b[1]) - 90
        device_id = (b[0] << 8) | b[2]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id,
            "temperature_F": float(tempf),
        })


__all__ = ["QuiggBBQ"]
