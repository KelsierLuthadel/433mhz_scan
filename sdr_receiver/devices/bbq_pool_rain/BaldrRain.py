"""@file
    Baldr / RainPoint Rain Gauge protocol.

    Copyright (C) 2023 Christian W. Zuckschwerdt <zany@triq.net>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Baldr / RainPoint Rain Gauge protocol.

For Baldr Wireless Weather Station with Rain Gauge.
See #2394

Only reports rain. There's a separate temperature sensor captured by Nexus-TH.

The sensor sends 36 bits 13 times, the packets are ppm modulated (distance coding)
with a pulse of ~500 us followed by a short gap of ~1000 us for a 0 bit or a long
~2000 us gap for a 1 bit, the sync gap is ~4000 us.

The data is grouped in 9 nibbles:

    II IF RR RR R

- I : 8 or 12-bit ID, could contain a model type nibble
- F : 4 bit, some flags
- R : 20 bit rain in inch/1000
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from .._helpers import _bits_to_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BaldrRain(OOKPPMDecoder):
    """Baldr / RainPoint Rain Gauge.

    OOK_PULSE_PPM, 36 bits.
    Layout: III III IF RR RR R (9 nibbles).
    ID = 12 bits, flags = 4 bits, rain_in = 20 bits (scale 0.001).
    No checksum  inherently low confidence.
    """

    name     = "Baldr-Rain"
    short_us = 1000.0
    long_us  = 2000.0
    reset_us = 5000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        b = _bits_to_bytes(bits[:36])
        if len(b) < 5:
            return None
        # Reject all-zero or all-0xFF
        if (b[0] == 0 and b[2] == 0 and b[3] == 0) or \
           (b[0] == 0xFF and b[2] == 0xFF and b[3] == 0xFF):
            return None
        id_     = (b[0] << 4) | (b[1] >> 4)
        flags   = b[1] & 0x0F
        rain_in = (b[2] << 12) | (b[3] << 4) | (b[4] >> 4)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":      id_,
            "flags":   flags,
            "rain_in": round(rain_in * 0.001, 3),
        })


__all__ = ["BaldrRain"]
