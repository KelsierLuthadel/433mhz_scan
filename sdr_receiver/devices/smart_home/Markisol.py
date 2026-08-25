"""Markisol (a.k.a E-Motion, BOFU, Rollerhouse, BF-30x, BF-415) curtains remote.

Copyright (C) 2021 Dan Stahlke <dan@stahlke.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Markisol curtains remote.

Protocol description:
Each frame starts with:
    hi 4886us
    lo 2470us
    hi 1647us
    lo 315us
Then follow 40 bits:
    zero: hi 670us, lo 320us
    one : hi 348us, lo 642us

This is OOK_PULSE_PWM encoding.  The frame is erroneously interpred as a bit (so bitbuffer_t reports
41 bits rather than 40).  We discard this bit during recording.  The last frame erroneosly picks up
an extra bit at the end; we ignore this as well.

Packet interpretation:
    16 bits - unique ID of remote
    16 bits - channel, zone, and control
    8  bits - checksum (all bytes, including this one, sum to 1)

The second pack of 16 bits is interwoven:
    buf[2] & 0x0f - channel, in the range 1-15
    buf[2] & 0x20 - bit 0 of zone
    buf[2] & 0xd0 - bits 0,2,3 of control
    buf[3] & 0x10 - bit 1 of control
    buf[3] & 0x80 - bit 1 of zone
    buf[3] & 0x6f - unknown; for my remotes (buf[3] & 0x6f) == 0x01 always
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Markisol(OOKPWMDecoder):
    """Markisol (Fenix / Teleco) awning / blind remote.

    OOK_PULSE_PWM, short=368 µs, long=704 µs, reset=2000 µs.
    41 raw bits: first bit discarded, remaining 40 bits reversed and inverted.
    5-byte payload; sum of all 5 bytes must equal 0x01 (mod 256).
    Fields: address[16] | channel[4] | control[4] (byte 2) | checksum.
    """
    name     = "Markisol-Remote"
    short_us = 368.0
    long_us  = 704.0
    reset_us = 2000.0
    n_bits   = 41

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 41:
            return None
        data = bits[1:41]               # discard first bit
        rev  = [1 - b for b in data[::-1]]  # reverse then invert
        b    = [bits_to_int(rev[i : i + 8]) for i in range(0, 40, 8)]
        if sum(b) & 0xFF != 0x01:
            return None
        address = (b[0] << 8) | b[1]
        channel = b[2] & 0x0F
        control = (b[2] >> 4) & 0x0F
        zone    = ((b[2] >> 5) & 0x1) | ((b[3] >> 6) & 0x2)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":      address,
            "channel": channel,
            "zone":    zone + 1,
            "control": control,
        })


__all__ = ["Markisol"]
