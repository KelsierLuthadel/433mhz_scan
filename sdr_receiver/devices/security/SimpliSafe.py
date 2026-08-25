"""Protocol of the SimpliSafe Sensors.

Copyright (C) 2018 Adam Callis <adam.callis@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Protocol of the SimpliSafe Sensors.

The data is sent leveraging a PiWM Encoding where a long is 1, and a short is 0

All bytes are sent with least significant bit FIRST (1000 0111 = 0xE1)

 2 Bytes   | 1 Byte       | 5 Bytes   | 1 Byte  | 1 Byte  | 1 Byte       | 1 Byte
 Sync Word | Message Type | Device ID | CS Seed | Command | SUM CMD + CS | Epilogue
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SimpliSafe(RawDecoder):
    """SimpliSafe Gen 2 home security system (OOK_PULSE_PIWM_DC, 500/1000 µs).

    Two identical 92-bit rows, sync 0xCC5F, checksum (seq+state)&0xFF.
    PIWM_DC encoding requires specialised demodulation.
    """

    name = "SimpliSafe"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["SimpliSafe"]
