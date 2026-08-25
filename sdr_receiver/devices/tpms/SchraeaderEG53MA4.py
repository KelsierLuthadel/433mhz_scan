"""Schrader TPMS protocol.

Copyright (C) 2016 Benjamin Larsson
and 2017 Christian W. Zuckschwerdt <zany@triq.net>

Schrader EG53MA4 TPMS decoder (GM vehicles).

Source: schraeder.c (schrader_EG53MA4_decode)
Modulation: OOK_PULSE_MANCHESTER_ZEROBIT, chip=123 µs, reset=300 µs
120-bit total; skip first 40 bits; data in bytes 5-14 (10 bytes)
Checksum: sum of bytes mod 256 = 0
Pressure in PSI (byte * 0.2); Temperature in deg C (deg F - 40 / 1.8)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _bits_to_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class SchraeaderEG53MA4(ManchesterDecoder):
    """Schrader EG53MA4 TPMS (GM)  OOK Manchester, sum checksum."""

    name     = "Schrader-EG53MA4"
    chip_us  = 123.0
    reset_us = 300.0
    n_bits   = 120
    inverted = False

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 120:
            return None
        # Skip first 40 bits (preamble/sync), use next 80 bits (10 bytes)
        data_bits = bits[40:120]
        b = _bits_to_bytes(data_bits)
        if len(b) < 10:
            return None
        if sum(b) & 0xFF != 0:
            return None

        sid   = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
        # Pressure in PSI (raw * 0.2), convert to kPa (* 6.895)
        pres_psi = b[4] * 0.2
        pres_kpa = round(pres_psi * 6.895, 1)
        # Temperature: stored in Fahrenheit units, offset −40
        temp_f = b[5] - 40
        temp_c = round((temp_f - 32) / 1.8, 1)

        return DecodedPacket.from_fields("Schrader-EG53MA4", freq_hz, {
            "id":            f"{sid:08x}",
            "pressure_kPa":  pres_kpa,
            "temperature_C": temp_c,
        })


__all__ = ["SchraeaderEG53MA4"]
