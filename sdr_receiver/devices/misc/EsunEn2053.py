"""Esun EN2053 two-channel BBQ thermometer.

Copyright (C) 2026 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Esun EN2053 two-channel BBQ thermometer.

Generic-brand two-probe wireless BBQ/meat thermometer, FCC ID 2APN2-EN2053
(Fuzhou Esun Electronic Co.), sold under various names.

The sensor sends 40 bits, OOK PPM modulated, repeated 9 times per
transmission with a longer row gap between repeats:

    .short gap  = 1024 us (0 bit)
    .long gap   = 2000 us (1 bit)
    .row gap    = 3952 us
    pulse width = 436 us

Data layout:

    PP 11 12 22 XX

- P: 8 bit fixed preamble/type 0xc0
- 1: 12 bit probe 1 temperature in Fahrenheit, whole degrees
- 2: 12 bit probe 2 temperature in Fahrenheit, whole degrees
- X: 8 bit checksum

A disconnected probe reads 0xfd6 (4054, or -42 as signed 12 bit).
Temperatures are transmitted in Fahrenheit regardless of the display unit setting.

The checksum packs four even-parity flags and a modulo-8 sum of the four
preceding bytes b[0]..b[3]:

- bits 0-2: (b[0] + b[1] + b[2] + b[3]) modulo 8
- bit 3: always 0
- bits 4-7: even parity of b[0], b[1], b[2], b[3] respectively
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EsunEn2053(OOKPPMDecoder):
    """Esun EN2053 dual probe thermometer."""
    name     = "Esun-EN2053"
    short_us = 1024.0
    long_us  = 2000.0
    reset_us = 7500.0
    n_bits   = 40

    _DISCONNECTED = 0xFD6

    def _parse(self, bits, freq_hz):
        if len(bits) < 40:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8)]
        if b[0] != 0xC0:
            return None
        probe1_raw = (b[1] << 4) | (b[2] >> 4)
        probe2_raw = ((b[2] & 0x0F) << 8) | b[3]
        # Lower 3 bits of b[4] = sum(b[0:4]) mod 8
        chk_calc = (b[0] + b[1] + b[2] + b[3]) & 0x07
        if chk_calc != (b[4] & 0x07):
            return None
        fields: dict = {}
        if probe1_raw != self._DISCONNECTED:
            fields["temperature_1_F"] = probe1_raw
            fields["temperature_1_C"] = round((probe1_raw - 32) * 5 / 9, 1)
        else:
            fields["probe_1"] = "disconnected"
        if probe2_raw != self._DISCONNECTED:
            fields["temperature_2_F"] = probe2_raw
            fields["temperature_2_C"] = round((probe2_raw - 32) * 5 / 9, 1)
        else:
            fields["probe_2"] = "disconnected"
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["EsunEn2053"]
