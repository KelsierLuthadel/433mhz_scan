"""Generic doorbell implementation for Elro DB286A devices.

Copyright (C) 2016 Fabian Zaremba <fabian@youremail.eu>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Generic doorbell implementation for Elro DB286A devices.

Note that each device seems to have two codes, which alternate
for every other button press.

short is 456 us pulse, 1540 us gap
long is 1448 us pulse, 544 us gap
packet gap is 7016 us

Example code: 37f62a6c80
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ElroDb286a(OOKPWMDecoder):
    """Elro DB286A doorbell.
    OOK_PULSE_PWM, 33 bits; trailing bit is padding  only first 32 used.
    short=0, long=1.  No checksum.
    """
    name     = "Elro-DB286A-Doorbell"
    short_us = 456.0
    long_us  = 1448.0
    reset_us = 8000.0
    n_bits   = 33

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        code = bits_to_int(bits[0:32])
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "code": f"{code:08X}",
        })


__all__ = ["ElroDb286a"]
