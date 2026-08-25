"""Thermor DG950 weather station.

Copyright (C) 2024 Nicolas Gagné, Bruno OCTAU (ProfBoc75)
Copyright (C) 2024 Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ThermorDG950(RawDecoder):
    """Thermor DG950 weather station.
    OOK_PULSE_PWM, 104 bits (9-bit rows x 13) with per-byte inversion.
    Multi-group additive checksum.  Complex encoding  stub.
    """
    name  = "Thermor-DG950"
    SHORT = 680    # us
    LONG  = 2100
    SYNC  = 1438
    RESET = 8000

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["ThermorDG950"]
