"""Schrader TPMS protocol.

Copyright (C) 2016 Benjamin Larsson
and 2017 Christian W. Zuckschwerdt <zany@triq.net>

Schrader TPMS decoder.

FCC-Id: MRXGG4

Packet payload: 1 sync nibble and 8 bytes data, 17 nibbles:

    0 12 34 56 78 9A BC DE F0
    7 f6 70 3a 38 b2 00 49 49
    S PF FI II II II PP TT CC

- S: sync
- P: preamble (0xf)
- F: flags
- I: id (28 bit)
- P: pressure from 0 bar to 6.375 bar, resolution of 25 mbar/hectopascal per bit
- T: temperature from -50 C to 205 C (1 bit = 1 temperature count 1 C)
- C: CRC8 from nibble 1 to E

Source: schraeder.c (schraeder_decode)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _bits_to_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class Schraeder(ManchesterDecoder):
    """Schrader TPMS (basic Gen1)  OOK Manchester, CRC-8."""

    name     = "Schrader-TPMS"
    chip_us  = 120.0
    reset_us = 480.0
    n_bits   = 68
    inverted = False

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Skip leading sync bits (look for 4 consecutive 0 bits then data)
        for start in range(min(8, len(bits) - 64)):
            seg = bits[start : start + 64]
            if len(seg) < 64:
                break
            b = _bits_to_bytes(seg)
            if len(b) < 8:
                continue
            if crc8(b[:7], 0x07, 0x00) != b[7]:
                continue

            sid    = bits_to_int(seg[0:28])
            status = bits_to_int(seg[28:36])
            pres   = round(bits_to_int(seg[36:44]) * 2.5, 0)
            temp   = bits_to_int(seg[44:52]) - 50

            return DecodedPacket.from_fields("Schrader-TPMS", freq_hz, {
                "id":            f"{sid:07x}",
                "status":        f"{status:02x}",
                "pressure_kPa":  pres,
                "temperature_C": temp,
            })
        return None


__all__ = ["Schraeder"]
