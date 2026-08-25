"""Decoder for TBH Archos devices.

Copyright (c) 2019 duc996 <duc_996@gmx.net>

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


class ArchosTbh(RawDecoder):
    """TBH weather sensor  FSK PCM with XOR-obfuscated payload."""
    name = "Archos-TBH"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["ArchosTbh"]
