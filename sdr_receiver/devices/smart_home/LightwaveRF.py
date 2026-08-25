"""LightwaveRF protocol.

Copyright (C) 2015 Tommy Vestermark

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

LightwaveRF protocol.

Stub for decoding test data only

Reference: https://wiki.somakeit.org.uk/wiki/LightwaveRF_RF_Protocol
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LightwaveRF(RawDecoder):
    """LightwaveRF 433 MHz home-automation system.

    OOK_PULSE_PPM, short=250 µs, long=1250 µs, reset=1500 µs.
    71-bit OOK frame; 4-stage decode: invert → bit-stuff → strip delimiters
    → nibble LUT.  Yields 10 nibbles (40 bits): parameter | subunit+cmd |
    id[24].  No checksum.
    Stub: complex multi-stage encoding not yet implemented.
    """
    name = "LightwaveRF"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # complex encoding not implemented


__all__ = ["LightwaveRF"]
