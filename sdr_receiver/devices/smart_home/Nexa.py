"""Nexa decoder.

Copyright (C) 2017 Christian Juncker Braedstrup

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Nexa decoder.
Might be similar to an x1527.
S.a. Kaku, Proove.

Tested devices:
- Magnetic sensor - LMST-606

Packet gap is 10 ms.

This device is very similar to the proove magnetic sensor.
The proove decoder will capture the OFF-state but not the ON-state
since the Nexa uses two different bit lengths for ON and OFF.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Nexa(OOKPPMDecoder):
    """Nexa / Proove / Ansluta smart-home remote (Self-learning protocol).

    OOK_PULSE_PPM, short=270 µs, long=1300 µs, reset=2800 µs.
    64 or 72 bits; not Manchester but ternary-encoded in the C decoder.
    Fields: id[26] | group[1] | state[1] | channel[2] | unit[2].
    Channel and unit bits are inverted.  No checksum.
    """
    name     = "Nexa"
    short_us = 270.0
    long_us  = 1300.0
    reset_us = 2800.0
    n_bits   = 64

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        n = len(bits)
        if n < 64:
            return None
        device_id = bits_to_int(bits[0:26])
        group     = bits[26]
        state     = bits[27]
        # channel and unit are stored inverted
        channel   = 3 - bits_to_int(bits[28:30])
        unit      = 3 - bits_to_int(bits[30:32])
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":      device_id,
            "group":   group,
            "state":   "on" if state else "off",
            "channel": channel + 1,
            "unit":    unit + 1,
        })


__all__ = ["Nexa"]
