"""Chrysler - Car Remote.

Copyright (C) 2024 Ethan Halsall

Chrysler - Car Remote (315 MHz).

Manufacturer: Chrysler

Supported Models:
- 56008761, 56008762 (FCC ID GQ43VT7T)
- 04686366, 56021903AA

The transmitter uses a fixed code message. This transmitter has 3 buttons which can
be pressed once to transmit a single message. Multiple buttons can be pressed down to
send unique codes. Data structure includes preamble (25 bits) and packets (49 and 48 bits).
Bytes are inverted and reflected. Format contains 32-bit remote ID, 4-bit button code,
unknown bits, multi-press indicator, and 8-bit checksum.
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


class ChryslerCarRemote(OOKPWMDecoder):
    """Chrysler Car Remote  315.1 MHz, OOK PWM, 48 bits.

    Bits are transmitted inverted and LSB-first per byte.  Checksum is the
    arithmetic sum of bytes 0-4 stored in byte 5.
    """
    name      = "Chrysler Car Remote"
    short_us  = 350.0     # 1× TE
    long_us   = 700.0     # 2× TE
    reset_us  = 17500.0   # 50× TE
    n_bits    = 48
    tolerance = 0.30      # ≈100 µs / 350 µs

    BUTTONS: dict[int, str] = {
        0x1: "Lock", 0x2: "Unlock", 0x4: "Trunk",
        0x8: "Panic", 0x3: "Lock+Unlock",
    }

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 48:
            return None
        raw = list(bits[:48])

        # The C decoder calls bitbuffer_invert then bitbuffer_reverse_each_byte
        inverted = [1 - b for b in raw]
        rev: list[int] = []
        for byte_idx in range(6):
            rev.extend(reversed(inverted[byte_idx * 8:(byte_idx + 1) * 8]))
        data = _bits_to_bytes(rev)

        # Sanity: reject trivially bad payloads
        s = sum(data[:5])
        if s == 0 or s >= 0xFF * 5:
            return None

        # Checksum: sum of bytes 0-4 must equal byte 5
        if (s & 0xFF) != data[5]:
            return None

        remote_id   = (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]
        button_code = (data[4] >> 4) & 0xF
        multi_press = bool(data[4] & 0x04)
        button_name = self.BUTTONS.get(button_code, f"0x{button_code:X}")

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"0x{remote_id:08X}",
            "button_code": button_code,
            "button": button_name,
            "multi_press": multi_press,
        })


__all__ = ["ChryslerCarRemote"]
