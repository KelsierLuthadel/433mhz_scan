"""SmartFire Proflame 2 remote protocol.

Copyright (C) 2021 Christian W. Zuckschwerdt <zany@triq.net>
based on protocol decode Copyright (C) 2020 johnellinwood

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


class Proflame2(RawDecoder):
    """SmartFire Proflame 2 remote  OOK PCM with G.E.T. Manchester encoding."""
    name = "Proflame2"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["Proflame2"]
