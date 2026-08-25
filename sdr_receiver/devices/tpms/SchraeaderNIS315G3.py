"""Schrader TPMS protocol.

Copyright (C) 2016 Benjamin Larsson
and 2017 Christian W. Zuckschwerdt <zany@triq.net>

Schrader NIS315G3 TPMS decoder (Nissan/Infiniti).

Source: schraeder.c (schrader_SMD3MA4_family_decode with NIS flag)
Modulation: OOK_PULSE_PCM, chip=120 µs, reset=480 µs
Same protocol as SMD3MA4 but pressure scale = 0.25 PSI/bit
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _find_pattern, _int_to_bits
if TYPE_CHECKING:
    from ...dsp import Pulse


class SchraeaderNIS315G3(OOKPCMDecoder):
    """Schrader NIS315G3 TPMS (Nissan/Infiniti)  OOK PCM + Manchester, 2-bit checksum."""

    name     = "Schrader-NIS315G3"
    chip_us  = 120.0
    reset_us = 480.0
    n_bits   = 120
    inverted = False

    _PREAMBLE = _int_to_bits(0xFF01, 16)

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        pos = _find_pattern(bits, self._PREAMBLE)
        if pos < 0:
            return None
        pos += 16
        decoded = _mc_decode(bits[pos:], 38)
        if len(decoded) < 38:
            return None

        data     = decoded[:36]
        check    = bits_to_int(decoded[36:38])
        expected = sum(data) % 4
        if check != expected:
            return None

        sid    = bits_to_int(decoded[0:28])
        pres_r = bits_to_int(decoded[28:36])
        # NIS315G3: 0.25 PSI/bit -> kPa
        pres   = round(pres_r * 0.25 * 6.895, 1)

        return DecodedPacket.from_fields("Schrader-NIS315G3", freq_hz, {
            "id":           f"{sid:07x}",
            "pressure_kPa": pres,
        })


__all__ = ["SchraeaderNIS315G3"]
