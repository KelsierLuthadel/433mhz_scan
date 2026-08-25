"""Eberle Instat 868r1 floor heating thermostat remote (FSK, differential Manchester).

Copyright (C) 2026 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Eberle Instat 868r1 floor heating thermostat remote (FSK, differential Manchester).

A 868 MHz 2-FSK transmitter used to learn, reset, and switch a receiver that
controls floor heating. Each button press sends 3 identical repeats.

Protocol reverse engineered from real captures and analysis in
https://github.com/merbanan/rtl_433/issues/1951 (readme.md, protocol.txt,
learn.txt/learn_Bitstream.txt and on_off.txt in the linked
dottoreD/rtl_433_tests fork), and cross-checked against 927 real "learn"
events and 36 real "on"/"off" events from that data.

Raw layout, 82 raw (chip) bits:

    30 bit fixed "beginning", then a 52 bit differential-Manchester-encoded
    "code part" that decodes to 25 bits: a fixed leading bit followed by
    24 data bits (6 nibbles).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EberleInstat868R1(RawDecoder):
    """Eberle Instat 868-R1 wireless room controller.

    FSK_PULSE_PCM, chip=400 µs, reset=8000 µs.
    Differential Manchester encoded; 82 raw bits → 25 decoded bits.
    24 data bits: id[12] | action[4] | action_data[4] | checksum[4].
    Checksum: (sum of all 6 nibbles) & 0xF == 0xB.
    Stub: FSK + differential Manchester decoding not supported.
    """
    name = "Eberle-Instat868"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK + differential Manchester decoding


__all__ = ["EberleInstat868R1"]
