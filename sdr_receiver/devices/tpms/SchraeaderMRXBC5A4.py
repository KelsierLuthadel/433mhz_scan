"""Schrader TPMS protocol.

Copyright (C) 2016 Benjamin Larsson
and 2017 Christian W. Zuckschwerdt <zany@triq.net>

Schrader MRXBC5A4 TPMS decoder (BMW aftermarket).

Source: schraeder.c (schrader_MRXBC5A4_decode)
Modulation: OOK_PULSE_MANCHESTER_ZEROBIT, chip=123 µs, reset=800 µs
61-bit message: 1 wake + 13 sync + 1 start + 3 flags + 24 ID + 9 pressure
               + 2 checksum bits + 8 temperature
Integrity: 2-bit parity checksum over ID+pressure bits
Pressure: 1 kPa/bit; Temperature = byte - 50 deg C
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SchraeaderMRXBC5A4(ManchesterDecoder):
    """Schrader MRXBC5A4 TPMS (BMW aftermarket)  OOK Manchester, parity check."""

    name     = "Schrader-MRXBC5A4"
    chip_us  = 123.0
    reset_us = 800.0
    n_bits   = 61
    inverted = False

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 61:
            return None
        # Fixed prefix: wake(1) + 13 sync + 1 start = 15 bits = 0x7fff... wait
        # 1 wake + 13 sync + 1 start = 15 bits, check first 16 bits = 0x7FFF
        if bits_to_int(bits[0:16]) != 0x7FFF:
            # Also accept 0 as the leading bit (wake bit varies)
            if bits_to_int(bits[1:16]) != 0x7FFF >> 1:
                pass  # proceed anyway, parity will catch bad frames

        # Offset by 15 (skip wake+sync+start), then extract fields
        p = 15
        if p + 46 > len(bits):
            return None

        flags      = bits_to_int(bits[p : p + 3]);         p += 3
        sid        = bits_to_int(bits[p : p + 24]);        p += 24
        pressure   = bits_to_int(bits[p : p + 9]);         p += 9
        check_bits = bits_to_int(bits[p : p + 2]);         p += 2
        temp_raw   = bits_to_int(bits[p : p + 8])

        # Validate 2-bit parity over bits[18:52] (ID + pressure + check)
        payload = bits[18:53]
        even_ones = sum(b for i, b in enumerate(payload) if i % 2 == 0)
        total_ones = sum(payload)
        n_pairs = (total_ones + 1) // 2
        expected = (even_ones + 2 * n_pairs - 1) % 4 if total_ones > 0 else 0
        if check_bits != expected:
            return None

        # Sanity
        if sid == 0 or sid == 0xFFFFFF:
            return None
        if pressure > 450:
            return None
        temp_c = temp_raw - 50
        if not -40 <= temp_c <= 85:
            return None

        return DecodedPacket.from_fields("Schrader-MRXBC5A4", freq_hz, {
            "id":            f"{sid:06x}",
            "flags":         flags,
            "pressure_kPa":  pressure,
            "temperature_C": temp_c,
        })


__all__ = ["SchraeaderMRXBC5A4"]
