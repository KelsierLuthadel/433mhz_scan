"""RadioHead ASK (generic) protocol.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Sensible Living Mini-Plant Moisture Sensor.

@todo Documentation needed.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class RadioheadASK(RawDecoder):
    """RadioHead ASK  OOK PCM with 6-to-4 bit symbol encoding."""
    name = "RadioHead-ASK"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["RadioheadASK"]
