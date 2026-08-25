"""Generic remote Blyss DC5-UK-WH as sold by B&Q.

Copyright (C) 2016 John Jore

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Generic remote Blyss DC5-UK-WH as sold by B&Q.

DC5-UK-WH pair with receivers, the codes used may be specific to a receiver - use with caution

warm-up pulse 5552 us, 2072 gap
short is 512 us pulse, 1484 us gap
long is 1508 us pulse, 488 us gap
packet gap is 6964 us
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BlyssDC5(OOKPWMDecoder):
    """Blyss DC5-UK-WH lamp remote.

    OOK_PULSE_PWM, short=500 µs, long=1500 µs, reset=8000 µs.
    40-bit payload (5 bytes).  Byte 4 must be 0x80.
    Bytes 0-3 form the device ID.  No checksum.
    """
    name     = "Blyss-DC5ukwh"
    short_us = 500.0
    long_us  = 1500.0
    reset_us = 8000.0
    n_bits   = 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 40:
            return None
        b = [bits_to_int(bits[i : i + 8]) for i in range(0, 40, 8)]
        if b[4] != 0x80:
            return None
        device_id = f"{b[0]:02x}{b[1]:02x}{b[2]:02x}{b[3]:02x}"
        return DecodedPacket.from_fields(self.name, freq_hz, {"id": device_id})


__all__ = ["BlyssDC5"]
