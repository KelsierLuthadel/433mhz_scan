"""Companion WTR001 Temperature Sensor decoder.

Copyright (C) 2019 Karl Lohner <klohner@thespill.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Companion WTR001 Temperature Sensor decoder.

The device uses PWM encoding with 2928 us for each pulse plus gap.
- Logical 0 is encoded as 732 us pulse and 2196 us gap,
- Logical 1 is encoded as 2196 us pulse and 732 us gap,
- SYNC is encoded as 1464 us and 1464 us gap.

A transmission starts with the SYNC,
there are 5 repeated packets, each ending with a SYNC.

Data layout (14 bits):

    DDDDDXTT TTTTTP

| Ordered Bits     | Description
|------------------|-------------
| 4,3,2,1,0        | DDDDD: Fractional part of Temperature. (DDDDD - 10) / 10
| 5                | X: Always 0 in testing. Maybe battery_OK or fixed
| 12,7,6,11,10,9,8 | TTTTTTT: Temperature in Celsius = (TTTTTTT + ((DDDDD - 10) / 10)) - 41
| 13               | P: Parity to ensure count of set bits in data is odd.

Temperature in Celsius = (bin2dec(bits 12,7,6,11,10,9,8) + ((bin2dec(bits 4,3,2,1,0) - 10) / 10) - 41

Published range of device is -29.9C to 69.9C
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class CompanionWtr001(OOKPWMDecoder):
    """Companion WTR001 Temperature Sensor."""
    name     = "Companion-WTR001"
    short_us = 732.0
    long_us  = 2196.0
    reset_us = 8000.0
    n_bits   = 14

    def _parse(self, bits, freq_hz):
        if len(bits) < 14:
            return None
        bits = [1 - b for b in bits]          # invert
        if bits[5] != 0:                       # fixed bit must be 0
            return None
        if sum(bits) % 2 == 0:                 # odd parity across all 14 bits
            return None
        # Fractional part assembled from non-sequential bit positions
        frac_val = bits_to_int([bits[4], bits[3], bits[2], bits[1], bits[0]])
        if not (10 <= frac_val <= 19):
            return None
        frac_dec = (frac_val - 10) / 10.0
        # Whole part assembled from non-sequential bit positions
        whole_val = bits_to_int([bits[12], bits[7], bits[6],
                                  bits[11], bits[10], bits[9], bits[8]])
        if not (11 <= whole_val <= 110):
            return None
        temp_c = round((whole_val + frac_dec) - 41.0, 1)
        if not (-30.0 <= temp_c <= 70.0):
            return None
        return DecodedPacket.from_fields(self.name, freq_hz,
            {"temperature_C": temp_c})


__all__ = ["CompanionWtr001"]
