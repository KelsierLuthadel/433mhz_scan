"""Clipsal CMR113 cent-a-meter power meter.

Copyright (C) 2021 Michael Neuling <mikey@neuling.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Clipsal CMR113 cent-a-meter power meter.

The demodulation comes in a few stages:

A) Firstly we look at the pulse lengths both high and low. These
   are demodulated using OOK_PULSE_PIWM_DC before we hit this
   driver. Any short pulse (high or low) is assigned a 1 and a
   long pulse (high or low) is assigned a 0. ie every pulse is a
   bit.

B) We then look for two patterns in this new bitstream:
    - 0b00 (ie long long from stream A)
    - 0b011 (ie long short short from stream A)

C) We start off with an output bit of '0'.  When we see a 0b00
   (from B), the next output bit is the same as the last
   bit. When we see a 0b011 (from B), the next output is
   toggled. If we don't see either of these patterns, we fail.

D) The output from C represents the final bitstream. This is 83
   bits repeated twice. There are some timestamps, transmitter
   IDs and CRC but all we decode below are the 3 current values
   which are 10 bits each representing AMPS/10.

Kudos to Jon Oxer for decoding this stream and putting it here:
https://github.com/jonoxer/CentAReceiver
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Cmr113(RawDecoder):
    """Clipsal CMR113 Power Meter  OOK PIWM DC (non-standard modulation)."""
    name = "CMR113"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["Cmr113"]
