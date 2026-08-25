"""bm5-v2 12V Automotive Wireless Battery Monitor.

Copyright (C) 2025 Cameron Murphy

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Bm5(OOKPWMDecoder):
    """bm5-v2 12V Battery Monitor."""
    name     = "BM5-v2"
    short_us = 225.0
    long_us  = 675.0
    reset_us = 6000.0
    n_bits   = 88

    def _parse(self, bits, freq_hz):
        if len(bits) < 88:
            return None
        b = bytearray(bits_to_int(bits[i:i + 8]) for i in range(0, 88, 8))
        # Reject trivially-zero messages
        if b[0] == 0 and b[1] == 0 and b[2] == 0 and b[10] == 0:
            return None
        if (sum(b[:10]) & 0xFF) != b[10]:
            return None
        device_id = (b[0] << 16) | (b[1] << 8) | b[2]
        soh       = b[3] >> 1
        charging  = bool(b[3] & 1)
        soc       = b[4] >> 1
        cranking  = bool(b[4] & 1)
        temp_mag  = b[5] >> 1
        temp_neg  = bool(b[5] & 1)
        temp_c    = -temp_mag if temp_neg else temp_mag
        v_cur     = ((b[7] << 8) | b[6]) * 0.000625   # little-endian
        v_start   = ((b[9] << 8) | b[8]) * 0.000625
        if soh > 100 or soc > 100:
            return None
        if not (0.0 <= v_cur <= 20.0) or not (0.0 <= v_start <= 20.0):
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id,
            "soh": soh, "charging": charging,
            "soc": soc, "cranking": cranking,
            "temperature_C": temp_c,
            "voltage_V": round(v_cur, 4),
            "start_voltage_V": round(v_start, 4),
            "mic": "CHECKSUM",
        })


__all__ = ["Bm5"]
