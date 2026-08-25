"""Example of a generic remote using PT2260/PT2262 SC2260/SC2262 EV1527 protocol.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Example of a generic remote using PT2260/PT2262 SC2260/SC2262 EV1527 protocol.

fixed bit width of 1445 us
short pulse is 357 us (1/4th)
long pulse is 1064 (3/4th)
a packet is 15 pulses, the last pulse (short) is sync pulse
packet gap is 11.5 ms

note that this decoder uses:
short-short (1 1 by the demod) as 0 (per protocol),
short-long (1 0 by the demod) as 1 (F per protocol),
long-long (0 0 by the demod) not used (1 per protocol).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Waveman(OOKPWMDecoder):
    """Waveman switch transmitter.

    OOK_PULSE_PWM, short=357 µs, long=1064 µs, reset=12000 µs.
    25 bits: even positions are 1 (padding), odd positions are data nibbles.
    12 data bits: id[4] | channel[4] | state[4].  State 0xe=ON, 0x6=OFF.
    """
    name     = "Waveman-Switch"
    short_us = 357.0
    long_us  = 1064.0
    reset_us = 12000.0
    n_bits   = 25

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 25:
            return None
        for i in range(0, 24, 2):
            if bits[i] != 1:
                return None
        data = [bits[i] for i in range(1, 25, 2)]   # 12 data bits
        nb = [bits_to_int(data[i : i + 4]) for i in range(0, 12, 4)]
        if nb[2] not in (0xe, 0x6):
            return None
        device_id = chr(ord('A') + (nb[0] & 0x7))
        channel   = (nb[1] & 0xF) + 1
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":      device_id,
            "channel": channel,
            "state":   "on" if nb[2] == 0xe else "off",
        })


__all__ = ["Waveman"]
