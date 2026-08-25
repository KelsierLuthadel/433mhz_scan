"""Somfy RTS.

Copyright (C) 2020 Matthias Schulz <mschulz@seemoo.tu-darmstadt.de>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Somfy RTS.

Protocol description:
The protocol is very well defined under the following two links:
[1] https://pushstack.wordpress.com/somfy-rts-protocol/
[2] https://patentimages.storage.googleapis.com/bd/ae/4f/bf24e41e0161ca/US8189620.pdf

Each frame consists of a preamble with hardware and software sync pulses followed by the manchester encoded data pulses.
A rising edge describes a data bit 1 and a falling edge a data bit 0. The preamble is different for the first frame and
for retransmissions. In the end, the signal is first decoded using an OOK PCM decoder and within the callback, only the
data bits will be manchester decoded.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SomfyRTS(OOKPCMDecoder):
    """Somfy RTS rolling-shutter remote.

    OOK_PULSE_PCM, chip=604 µs, reset=10000 µs.
    Manchester encoded: rising edge=1, falling edge=0.
    7-byte payload (56 data bits = 112 PCM chips).
    Checksum: XOR all 7 bytes, fold upper/lower nibbles → must be 0.
    Descramble: frame[i] ^= frame[i-1] for i in 1..6.
    Fields: key[8] | cmd[4] | chk[4] | rolling_code[16] | address[24].
    """
    name     = "Somfy-RTS"
    chip_us  = 604.0
    reset_us = 10000.0
    n_bits   = 112   # 56 Manchester pairs

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 112:
            return None
        # Manchester decode: pairs of PCM chips
        decoded: list[int] = []
        for i in range(0, 112, 2):
            a, bb = bits[i], bits[i + 1]
            if a == 0 and bb == 1:
                decoded.append(1)
            elif a == 1 and bb == 0:
                decoded.append(0)
            else:
                return None
        b = [bits_to_int(decoded[i : i + 8]) for i in range(0, 56, 8)]
        # XOR nibble checksum on scrambled frame
        xval = 0
        for byte in b:
            xval ^= byte
        if (xval ^ (xval >> 4)) & 0xF != 0:
            return None
        # descramble
        for i in range(1, 7):
            b[i] ^= b[i - 1]
        cmd          = (b[1] >> 4) & 0xF
        rolling_code = (b[2] << 8) | b[3]
        address      = (b[6] << 16) | (b[5] << 8) | b[4]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           address,
            "cmd":          cmd,
            "rolling_code": rolling_code,
        })


__all__ = ["SomfyRTS"]
