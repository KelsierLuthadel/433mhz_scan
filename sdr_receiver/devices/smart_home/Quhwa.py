"""Quhwa HS1527.

Copyright (C) 2016 Ask Jakobsen

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Quhwa HS1527.

Tested devices:
QH-C-CE-3V (which should be compatible with QH-832AC),
also sold as "1 by One" wireless doorbell
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Quhwa(OOKPWMDecoder):
    """Quhwa HS1527-based doorbell remote.

    OOK_PULSE_PWM, short=360 µs, long=1070 µs, reset=6600 µs.
    18 bits inverted; ID = bytes 0-1 of inverted stream.
    Validity: (inv_b1 & 0x03) == 0x03; ID must be non-zero.
    """
    name     = "Quhwa-Doorbell"
    short_us = 360.0
    long_us  = 1070.0
    reset_us = 6600.0
    n_bits   = 18

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 18:
            return None
        inv = [1 - b for b in bits[:18]]
        b0  = bits_to_int(inv[0:8])
        b1  = bits_to_int(inv[8:16])
        if (b1 & 0x03) != 0x03:
            return None
        if b0 == 0 and b1 == 0:
            return None
        device_id = (b0 << 8) | b1
        return DecodedPacket.from_fields(self.name, freq_hz, {"id": device_id})


__all__ = ["Quhwa"]
