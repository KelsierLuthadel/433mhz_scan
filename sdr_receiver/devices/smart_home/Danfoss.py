"""Danfoss CFR Thermostat sensor protocol.

Copyright (C) 2016 Tommy Vestermark

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Danfoss CFR Thermostat sensor protocol.

Manual: http://na.heating.danfoss.com/PCMPDF/Vi.88.R1.22%20CFR%20Thrm.pdf

No protocol information found, so protocol is reverse engineered.
Sensor uses FSK modulation and Pulse Code Modulated (direct bit sequence) data.

The package starts with a long (~128 bit) synchronization preamble (0xaa).
Sensor data consists of 21 nibbles of 4 bit, which are encoded with a 4b/6b encoder, resulting
in an encoded sequence of 126 bits (~16 encoded bytes).

Nibble content:

- #0 -#2  -- Prefix - always 0xE02 (decoded)
- #3 -#6  -- Sensor ID
- #7      -- Message Count. Rolling counter incremented at each unique message.
- #8      -- Switch setting -> 2="day", 4="timer", 8="night"
- #9 -#10 -- Temperature decimal: value/256
- #11-#12 -- Temperature integer (in Celsius)
- #13-#14 -- Set point decimal: value/256
- #15-#16 -- Set point integer (in Celsius)
- #17-#20 -- CRC16, poly 0x1021, includes nibble #1-#16
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Danfoss(RawDecoder):
    """Danfoss CFR radiator thermostat.

    FSK_PULSE_PCM, chip=100 µs, reset=500 µs.  Header 0x365C.
    4b/6b encoded payload → 21 nibbles.  Fields: prefix[3] | id[4] |
    counter[1] | switch[1] | temp_dec[2] | temp_int[2] | setp_dec[2] |
    setp_int[2] | CRC-16 (poly=0x1021, init=0x0000).
    Stub: FSK demodulation and 4b/6b decoding not supported.
    """
    name = "Danfoss-CFR"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK + 4b/6b decoding


__all__ = ["Danfoss"]
