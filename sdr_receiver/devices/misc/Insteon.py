"""Insteon RF decoder.

Copyright (C) 2020 Peter Shipley

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Insteon RF decoder.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Insteon(RawDecoder):
    """Insteon RF  FSK PCM with Manchester-encoded index/data blocks."""
    name = "Insteon"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["Insteon"]
