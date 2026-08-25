"""X10 Security sensor decoder.

Copyright (C) 2018 Anthony Kava

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

X10 Security sensor decoder.

Each packet starts with a sync pulse of 9000 us and 4500 us gap.
The message is OOK PPM encoded with 562 us pulse and long gap (0 bit)
of 1687 us or short gap (1 bit) of 562 us. There are 41 bits, the
message is repeated 5 times with a packet gap of 40000 us.

The protocol has a lot of similarities to the NEC IR protocol

Bits 0-7 are first part of the device ID
Bits 8-11 should be identical to bits 0-3
Bits 12-15 should be the XOR function of bits 4-7
Bits 16-23 are the code/message sent
Bits 24-31 should be the XOR function of bits 16-23
Bits 32-39 are the second part of the device ID
Bit 40 is CRC checksum (even parity)

Tested with American sensors operating at 310 MHz
e.g., rtl_433 -f 310.558M

Tested with European/International sensors, DS18, KR18 and MS18 operating at 433 MHz
e.g., rtl_433

American sensor names ends with an 'A', like DS18A, while European/International
sensor names ends with an 'E', like MS18E

Based on code provided by Willi 'wherzig' in issue #30 (2014-04-21)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class X10Sec(OOKPPMDecoder):
    """X10 Security RF sensor (DS10A, MS10A, KR10A, etc.).

    OOK_PULSE_PPM, short=562 µs, long=1687 µs, reset=6000 µs.
    41 bits: id_a[8] | nibble_dup[4] | nibble_xor[4] | code[8] | code_xor[8] | id_b[8] | parity[1].
    Bytes 0/1: upper nibbles equal; lower nibbles complement.
    Bytes 2/3: XOR == 0xFF.  Even bit parity across all 41 bits.
    """
    name     = "X10-Security"
    short_us = 562.0
    long_us  = 1687.0
    reset_us = 6000.0
    n_bits   = 41

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 41:
            return None
        b = [bits_to_int(bits[i : i + 8]) for i in range(0, 40, 8)]
        parity_bit = bits[40]
        if (b[0] >> 4) != (b[1] >> 4):
            return None
        if ((b[0] & 0x0F) ^ (b[1] & 0x0F)) != 0x0F:
            return None
        if (b[2] ^ b[3]) != 0xFF:
            return None
        # even parity: XOR of all bytes + parity bit should fold to 0
        xval = b[0] ^ b[1] ^ b[2] ^ b[3] ^ b[4] ^ (parity_bit << 7)
        xval ^= xval >> 4
        xval ^= xval >> 2
        xval ^= xval >> 1
        if xval & 1:
            return None
        device_id = (b[0] << 8) | b[4]
        code      = b[2]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":   device_id,
            "code": code,
        })


__all__ = ["X10Sec"]
