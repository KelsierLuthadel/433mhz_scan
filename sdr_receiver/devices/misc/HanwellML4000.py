"""Hanwell ML/RL4000-series Radiologger temperature/humidity sensor.

Copyright (C) 2026 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Hanwell ML/RL4000-series Radiologger temperature/humidity sensor.

Likely an ML4106/RL4106 in its 12-bit radio mode. FSK PWM, centered at
434.052 MHz with tones roughly +21.9/+26.3 kHz either side -- midpoint
434.076 MHz matches the documented Hanwell 434.075 MHz channel.
Hanwell ML4106 datasheet: https://www.datenlogger-store.de/mwdownloads/download/link/id/788
ML4000 8/12-bit radio mode guide: https://www.catec.nl/uploads/pdf/Han-ml4000-guide_810.pdf

40 data bits follow, each received byte bit-reversed (least-significant bit
transmitted first within a byte).

Data layout, after reverse8() on each byte:

    II HHHH TTTT hhhh|tttt CC

- I: 8 bit transmitter ID
- H: top 8 bits of a 12 bit humidity raw count
- T: top 8 bits of a 12 bit temperature raw count
- h/t: bottom 4 bits of humidity, then bottom 4 bits of temperature
- C: 8 bit additive checksum of the preceding 4 bytes
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HanwellML4000(RawDecoder):
    """Hanwell ML/RL4000-series Radiologger  FSK PWM modulation."""
    name = "Hanwell-ML4000"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["HanwellML4000"]
