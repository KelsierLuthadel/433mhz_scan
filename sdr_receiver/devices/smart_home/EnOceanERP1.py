"""EnOcean ERP1.

Copyright (C) 2021 Christoph M. Wintersteiger <christoph@winterstiger.at>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

EnOcean Radio Protocol 1.

- 868.3Mhz ASK, 125kbps, inverted, 8/12 coding
- Spec: https://www.enocean.com/erp1/
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EnOceanERP1(RawDecoder):
    """EnOcean ERP1 energy-harvesting sensor protocol.

    OOK_PULSE_PCM, chip=8 µs, reset=800 µs.
    Preamble: 0x55 0x20 (11 bits).  8-of-12 encoding (3+1parity+3+1parity+2+2).
    CRC-8: poly=0x07, init=0x00 over decoded payload.
    Stub: 8-of-12 decoding not yet implemented.
    """
    name = "EnOcean-ERP1"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # 8-of-12 decoding not implemented


__all__ = ["EnOceanERP1"]
