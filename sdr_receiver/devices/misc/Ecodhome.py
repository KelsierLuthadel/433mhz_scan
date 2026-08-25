"""Decoder for EcoDHOME Smart Socket and MCEE Solar monitor.

Copyright (C) 2020 Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Ecodhome(RawDecoder):
    """EcoDHOME Smart Socket and MCEE Solar monitor  FSK PCM."""
    name = "EcoDHOME"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["Ecodhome"]
