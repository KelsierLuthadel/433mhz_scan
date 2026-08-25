"""Watts Vision thermostat (CC110L-based FSK protocol).

Copyright (C) 2026 Benjamin Larsson <banan@ludd.ltu.se>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Watts Vision thermostat (CC110L-based FSK protocol).

Not to be confused with the Watts WFHT-RF thermostat (see watts_wfht_rf.c),
an unrelated older OOK/PWM device.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class WattsVision(RawDecoder):
    """Watts Vision wireless thermostat system.

    FSK_PULSE_PCM, chip=26 µs, reset=1000 µs.
    Preamble: 0xaa 0xd3 0x91 0xd3 0x91 (40 bits).
    Frame: len[8] | src[32] | marker[8]=0xc6 | dst[32] | records[var] |
    CRC-MODBUS[16] | CRC-CMS[16].
    Stub: FSK demodulation not supported in OOK pipeline.
    """
    name = "Watts-Vision"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK demodulation


__all__ = ["WattsVision"]
