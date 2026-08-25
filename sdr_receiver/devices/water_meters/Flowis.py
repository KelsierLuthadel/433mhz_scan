"""@file
    Flowis water meter.

    Copyright (C) 2023 Benjamin Larsson

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Heavily based on marlec_solar.c
    Copyright (C) 2021 Christian W. Zuckschwerdt <zany@triq.net>

Flowis water meter.

There are several different message types with different message lengths.
All signals are transmitted with a preamble (0xA or 0x5) and then the
syncword d391 d391.

Message layout type 1 (0x15 bytes of length):
- S 32b: 2 x 16 bit sync words d391 d391
- L  8b: message length
- Y  8b: message type (1 and 2 has been observed)
- I 32b: meter id
- ?  8b: unknown
- T 32b: timestamp, bitpacked
- V 32b: Volume in m3
- A  8b: Alarm
- B  8b: Backflow
- C 16b: CRC-16 with poly=0x8005 and init=0xFFFF over data after sync
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Flowis(RawDecoder):
    """Flowis flow meters.

    FSK_PULSE_PCM, chip=10 us, reset=5000 us.
    Preamble: 0xaa 0xaa 0xd3 0x91 0xd3 0x91 (48 bits sync).
    CRC-16/ARC (poly=0x8005, init=0xFFFF) over data after sync.
    Payload (Type-1 messages):
      byte[4]      – message length
      byte[5]      – message type
      bytes[6:10]  – meter ID (32-bit)
      bytes[10:14] – timestamp (bitpacked: year/month/day/hour/min/sec)
      bytes[11:14] – volume (24-bit, cubic metres)
      byte[14]     – backflow flag
      byte[15]     – alarm flags
    """
    name = "Flowis"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: FSK demodulation not yet implemented.
        return None


__all__ = ["Flowis"]
