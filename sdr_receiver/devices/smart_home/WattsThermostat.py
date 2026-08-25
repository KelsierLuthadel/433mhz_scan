"""Watts WFHT-RF Thermostat.

Copyright (C) 2022 Adne Hovda <aadne@hovda.no>
based on protocol decoding by Christian W. Zuckschwerdt <zany@triq.net>
and Adne Hovda <aadne@hovda.no>

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


def _reflect(val: int, n: int) -> int:
    """Bit-reverse the lowest *n* bits of *val*."""
    result = 0
    for _ in range(n):
        result = (result << 1) | (val & 1)
        val >>= 1
    return result


class WattsThermostat(OOKPWMDecoder):
    """Watts WFHT-RF wireless thermostat (OOK variant).

    OOK_PULSE_PWM, short=260 µs, long=600 µs, reset=900 µs.
    54 bits: preamble[8]=0xA5 | id[16] | flags[4] | temp[9] | setpoint[9] | chk[8].
    ID, temperature and setpoint bytes are reflected.
    Checksum: 8-bit sum of reflected ID bytes, flags, temp lo-byte, setpoint lo-byte.
    """
    name     = "Watts-WFHT"
    short_us = 260.0
    long_us  = 600.0
    reset_us = 900.0
    n_bits   = 54

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 54:
            return None
        preamble = bits_to_int(bits[0:8])
        if preamble != 0xA5:
            return None
        id_hi    = _reflect(bits_to_int(bits[8:16]),  8)
        id_lo    = _reflect(bits_to_int(bits[16:24]), 8)
        device_id = (id_hi << 8) | id_lo
        flags    = bits_to_int(bits[24:28])
        temp_raw = _reflect(bits_to_int(bits[28:37]), 9)
        setp_raw = _reflect(bits_to_int(bits[37:46]), 9)
        chk_rx   = bits_to_int(bits[46:54])
        chk_calc = (id_hi + id_lo + (flags << 4) + (temp_raw & 0xFF)
                    + (setp_raw & 0xFF)) & 0xFF
        if chk_rx != chk_calc:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           device_id,
            "temperature_C": round(temp_raw / 10.0, 1),
            "setpoint_C":    round(setp_raw / 10.0, 1),
            "pairing":       int(bool(flags & 1)),
        })


__all__ = ["WattsThermostat"]
