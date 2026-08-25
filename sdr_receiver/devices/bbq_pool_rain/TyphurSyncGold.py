"""@file
    Typhur Sync Gold meat thermometer probe (Dual/Quad variants).

    Copyright (C) 2026 Benjamin Larsson

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Typhur Sync Gold meat thermometer probe (Dual/Quad variants).

FSK_PCM at 12.5 us/bit, long 0xaa preamble, 16 bit sync word 0x5754, 24 byte payload:

    ID:24h ?:8h STATUS:8h ?:8h T1:16h T2:16h T3:16h T4:16h T5:16h
    AMBIENT:16h BATTERY:16h COUNTER:16h CRC:16h

- ID: 24 bit, one per physical probe
- STATUS: bit 3 set when the probe is seated in its charging base
- T1-T5: probe temperature sensors, little-endian, scale 0.01 C
- AMBIENT: little-endian, scale 0.1 C
- BATTERY: little-endian, scale 0.01 V
- COUNTER: little-endian, increments every transmission
- CRC: CRC-16 poly 0x8005 init 0x0000 over the preceding 22 bytes
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TyphurSyncGold(RawDecoder):
    """Typhur Sync Gold meat thermometer probe (stub  FSK_PULSE_PCM).

    Sync word 0x5754; 24-byte payload with CRC-16 poly=0x8005.
    Five probe temperatures, ambient, battery voltage, counter.
    Requires FSK demodulation; returns None in OOK capture mode.
    """

    name = "Typhur-SyncGold"

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        return None  # FSK_PULSE_PCM  requires FSK demodulation


__all__ = ["TyphurSyncGold"]
