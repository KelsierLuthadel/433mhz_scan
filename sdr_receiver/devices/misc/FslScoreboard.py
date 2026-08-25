"""FSL Cricket Scoreboard Controller.

Copyright 2026 David Woodhouse <dwmw2@infradead.org>

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


class FslScoreboard(RawDecoder):
    """FSL Cricket Scoreboard Controller  FSK PCM with Manchester encoding."""
    name = "FSL-Scoreboard"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["FslScoreboard"]
