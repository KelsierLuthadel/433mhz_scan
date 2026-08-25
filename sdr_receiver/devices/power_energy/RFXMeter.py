"""@file
    RFXMeter / RFXPower decoder.

    Copyright (C) 2022 Christian W. Zuckschwerdt <zany@triq.net>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

RFXMeter / RFXPower decoder.

S.a. https://github.com/merbanan/rtl_433/issues/2141

RFXMeter uses an X10RF-like frame with some variations.
The device uses PPM encoding,
- 0 is encoded as 0.5 ms pulse and 0.5 ms gap,
- 1 is encoded as 0.5 ms pulse and 1.5 ms gap.

A message is 48 bit / 6 bytes long:
- 2 bytes address (byte 1 is byte 0 with nibbles complemented)
- 3 bytes counter value (MSB first)
- 1 byte: message type (upper nibble) + nibble checksum (lower nibble)

The 4 bit checksum is a nibble sum over the whole message, complemented to 0xf.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class RFXMeter(OOKPPMDecoder):
    """RFXMeter wireless pulse counter / energy sensor.

    Modulation: OOK_PULSE_PPM.
    Frame (48 bits, 6 bytes):
        bytes 0-1: address  upper nibbles are one's-complements of each other
        bytes 2-4: 24-bit pulse counter (MSB first)
        byte 5  : message type (upper nibble) + nibble checksum (lower nibble)
    Checksum: sum of all 12 nibbles across all 6 bytes, masked to 4 bits, == 0xF.
    """
    name     = "RFXMeter"
    short_us = 500.0
    long_us  = 1_500.0
    reset_us = 5_000.0
    n_bits   = 48

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 48:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 48, 8)]
        # Address integrity: upper nibbles must be bitwise complements
        if (b[0] ^ b[1]) & 0xF0 != 0xF0:
            return None
        # Nibble checksum
        if sum((x >> 4) + (x & 0xF) for x in b) & 0xF != 0xF:
            return None
        counter  = (b[2] << 16) | (b[3] << 8) | b[4]
        msg_type = (b[5] >> 4) & 0xF
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":        b[0],
            "msg_type":  msg_type,
            "msg_value": counter,
            "mic":       "CHECKSUM",
        })


__all__ = ["RFXMeter"]
