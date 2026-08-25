"""@file
    ERT Interval Data Message (IDM) and Interval Data Message (IDM) for Net Meters.

    Copyright (C) 2020 Peter Shipley <peter.shipley@gmail.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Freq 912600155

This file contains support callbacks for both IDM and NetIDM given the similarities.

Currently the code is unable to differentiate between the two similar protocols thus
both will respond to the same packet. As of this time I am unable to find any
documentation on how to differentiate IDM and NetIDM packets as both use identical
Sync ID / Packet Type / length / App Version ID and CRC.

https://github.com/bemasher/rtlamr/wiki/Protocol
http://www.gridinsight.com/community/documentation/itron-ert-technology/
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ErtIdm(RawDecoder):
    """ERT IDM / NetIDM electricity/gas/water meter interval data message.

    OOK_PULSE_MANCHESTER_ZEROBIT, chip=30 us, gap=20000 us, reset=20000 us.
    Frame sync pattern: 0x16 0xA3 0x1C (3 bytes).
    Packet: 92 bytes (720 bits).
    CRC-16/CCITT-FALSE: poly=0x1021, init=0xD895 over bytes[2:88].
    IDM packet type 0x1C; NetIDM packet type 0x1D.
    Key fields:
      bytes[2]    – packet type
      bytes[3]    – packet length
      bytes[5]    – application version
      bytes[6]    – endpoint type
      bytes[7:11] – endpoint ID (32-bit BE)
      bytes[27:31]– last consumption count (32-bit BE)
      bytes[31:84]– differential consumption intervals (47 × 9-bit values)
      bytes[84:86]– transmit time offset
      bytes[86:88]– meter ID CRC
      bytes[88:90]– packet CRC
    """
    name = "ERT-IDM"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: complex 720-bit IDM/NetIDM protocol with differential consumption
        # intervals not yet implemented.
        return None


__all__ = ["ErtIdm"]
