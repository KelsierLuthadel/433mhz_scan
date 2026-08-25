"""Vaillant VRT 340f (calorMatic 340f) central heating control.

Copyright (C) 2017 Reinhold Kainhofer <reinhold@kainhofer.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Vaillant VRT 340f (calorMatic 340f) central heating control.

    http://wiki.kainhofer.com/hardware/vaillantvrt340f

The data is sent differential Manchester encoded
with bit-stuffing (after five 1 bits an extra 0 bit is inserted)

All bytes are sent with least significant bit FIRST (1000 0111 = 0xE1)

    0x00 00 7E | 6D F6 | 00 20 00 | 00 | 80 | B4 | 00 | FD 49 | FF 00
      SYNC+HD. | DevID | CONST?   |Rep.|Wtr.|Htg.|Btr.|Checksm| EPILOGUE

- CONST? ... Unknown, but constant in all observed signals
- Rep.   ... Repeat indicator: 0x00=original signal, 0x01=first repeat
- Wtr.   ... pre-heated Water: 0x80=ON, 0x88=OFF (bit 8 is always set)
- Htg.   ... Heating: 0x00=OFF, 0xB4=ON (2-point), 0x01-0x7F=target heating water temp
             (bit 8 indicates 2-point heating mode, bits 1-7 the heating water temp)
- Btr.   ... Battery: 0x00=OK, 0x01=LOW
- Checksm... Checksum (2-byte signed int): = -sum(bytes 4-12)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class VaillantVRT340F(RawDecoder):
    """Vaillant VRT 340f wireless thermostat.

    OOK_PULSE_DMC (Differential Manchester), chip=836 µs, long=1648 µs,
    reset=4000 µs, tolerance=120 µs.
    128-bit frame: sync[24] | id[16] | const[24] | repeat[8] | heat_flags[8] |
    mode_temp[8] | battery[8] | checksum[16].
    Checksum: two's complement of sum(bytes 4-12).
    Stub: Differential Manchester decoding not yet implemented.
    """
    name = "Vaillant-VRT340F"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires differential Manchester decoding


__all__ = ["VaillantVRT340F"]
