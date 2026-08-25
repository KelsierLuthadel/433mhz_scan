"""Honeywell CM921 Thermostat.

Copyright (C) 2020 Christoph M. Wintersteiger <christoph@winterstiger.at>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Honeywell CM921 Thermostat (subset of Evohome).

868Mhz FSK, PCM, Start/Stop bits, reversed, Manchester.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HoneywellCM921(RawDecoder):
    """Honeywell CM921 wireless thermostat (FSK_PULSE_PCM, 26 µs chip).

    Complex FSK protocol with Manchester payload and many command types.
    Requires FSK demodulation pipeline.
    """

    name = "Honeywell-CM921"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["HoneywellCM921"]
