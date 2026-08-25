"""DirecTV RC66RX Remote Control decoder.

Copyright (C) 2019 Karl Lohner <klohner@thespill.com>

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


class DirecTV(RawDecoder):
    """DirecTV RC66RX Remote Control  FSK PCM with DPWM encoding."""
    name = "DirecTV-RC66RX"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["DirecTV"]
