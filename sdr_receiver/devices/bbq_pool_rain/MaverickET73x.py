"""@file
    Maverick ET-73.

    Copyright (C) 2018 Benjamin Larsson

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Maverick ET-73 / ET-732 / ET-733 BBQ Sensor.

Manchester-encoded variant with LFSR session digest.

Preamble: raw 0x55 0x66 0x6a → decoded 0xfa8 (12 bits).
Payload: PRE:12h FLAG:4h T1:10d T2:10d DIGEST:16h
Temperatures: raw - 532 = degrees C.
LFSR digest (gen=0x8810, init=0xdd38) used to derive session ID.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from .._helpers import _bits_to_bytes, _lfsr_digest16
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class MaverickET73x(ManchesterDecoder):
    """Maverick ET-732/733 BBQ Sensor.

    OOK_PULSE_MANCHESTER_ZEROBIT, chip=230 us.
    104 raw half-bits → 52 Manchester-decoded bits.
    Preamble: raw 0x55 0x66 0x6a → decoded 0xfa8 (12 bits).
    Payload: PRE:12h FLAG:4h T1:10d T2:10d DIGEST:16h
    Temperatures: raw - 532 = degrees C.
    LFSR digest (gen=0x8810, init=0xdd38) used to derive session ID.
    """

    name     = "Maverick-ET73x"
    chip_us  = 230.0
    reset_us = 4000.0
    n_bits   = 52

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 52:
            return None
        pre = bits_to_int(bits[0:12])
        if pre != 0xfa8:
            return None
        flags  = bits_to_int(bits[12:16])
        temp1  = bits_to_int(bits[16:26])
        temp2  = bits_to_int(bits[26:36])
        digest = bits_to_int(bits[36:52])

        temp1_c = round(temp1 - 532.0, 2)
        temp2_c = round(temp2 - 532.0, 2)

        status = {2: "default", 7: "init"}.get(flags, "unknown")

        # Derive session ID via LFSR digest over FTt nibbles
        chk_data = _bits_to_bytes(bits[12:36])  # 3 bytes covering FLAG+T1+T2
        if len(chk_data) >= 3:
            computed = _lfsr_digest16(chk_data[:3], 0x8810, 0xdd38)
            session_id = computed ^ digest
        else:
            session_id = digest

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": session_id,
            "status": status,
            "temperature_1_C": temp1_c,
            "temperature_2_C": temp2_c,
        })


__all__ = ["MaverickET73x"]
