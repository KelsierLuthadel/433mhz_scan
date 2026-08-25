"""Schrader TPMS protocol.

Copyright (C) 2016 Benjamin Larsson
and 2017 Christian W. Zuckschwerdt <zany@triq.net>

Schrader SMD3MA4 TPMS decoder (Subaru).

Source: schraeder.c (schrader_SMD3MA4_family_decode)
Modulation: OOK_PULSE_PCM, chip=120 µs, reset=480 µs
16-bit preamble in NRZ stream + 38 Manchester-encoded data bits
2-bit addition checksum mod 4
Pressure = raw * 0.2 PSI (scaled) -> kPa; Temperature = raw - 40 deg C
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _find_pattern, _int_to_bits
if TYPE_CHECKING:
    from ...dsp import Pulse


_PREAMBLE = _int_to_bits(0xFF01, 16)


class SchraeaderSMD3MA4(OOKPCMDecoder):
    """Schrader SMD3MA4 TPMS (Subaru)  OOK PCM + Manchester, 2-bit checksum."""

    name     = "Schrader-SMD3MA4"
    chip_us  = 120.0
    reset_us = 480.0
    n_bits   = 120   # preamble chips + Manchester data chips
    inverted = False

    _PREAMBLE = _int_to_bits(0xFF01, 16)  # typical preamble pattern

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        pos = _find_pattern(bits, self._PREAMBLE)
        if pos < 0:
            return None
        pos += 16
        decoded = _mc_decode(bits[pos:], 38)
        if len(decoded) < 38:
            return None

        # 2-bit checksum: last 2 bits verified by (sum of all 36 data bits) mod 4
        data     = decoded[:36]
        check    = bits_to_int(decoded[36:38])
        expected = sum(data) % 4
        if check != expected:
            return None

        sid    = bits_to_int(decoded[0:28])
        pres_r = bits_to_int(decoded[28:36])
        # SMD3MA4: 0.2 PSI/bit -> kPa
        pres   = round(pres_r * 0.2 * 6.895, 1)

        return DecodedPacket.from_fields("Schrader-SMD3MA4", freq_hz, {
            "id":           f"{sid:07x}",
            "pressure_kPa": pres,
        })


__all__ = ["SchraeaderSMD3MA4"]
