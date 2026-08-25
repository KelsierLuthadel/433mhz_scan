"""Elsner Solexa 230V wind/light/temperature handset and sensor.

Copyright (C) 2026 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Elsner Solexa 230V handset and outdoor sensor (wind/temperature/light,
controlling a roller shutter/sunblind).

https://github.com/merbanan/rtl_433/issues/2798

FSK, Manchester coded with a fixed leading zero bit (IEEE 802.3-style,
chip width ~11 us), reported at 868.2 MHz. A long 0xAA-style alternating
preamble is followed by a fixed anchor byte 0x0a, then the on-air frame:

    SSSS SSSS PPPP...PPPP CCCC

- S: 4 byte sync/header region, constant 0xcead93ba on air.
- P: 32 byte payload (raw on-air bytes p0..p31).
- C: CRC-16 (poly 0x1021, init 0x68b3) over the preceding 36 on-air bytes.

FSK + descrambler path not yet implemented.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ElsnerSolexa(RawDecoder):
    """Elsner Solexa 230V weather sensor.
    FSK_PULSE_MANCHESTER_ZEROBIT, 304 bits, LFSR descrambler G(x)=x^7+x^5+1.
    CRC-16 poly=0x1021 init=0x68B3.
    FSK + descrambler path not yet implemented.
    """
    name = "Elsner-Solexa-230V"
    SYNC_WORD = 0x68B3

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["ElsnerSolexa"]
