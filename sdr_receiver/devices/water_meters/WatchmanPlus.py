"""@file
    Kingspan/Watchman Plus (Niveau) oil tank monitor, older PWM probe sensor.

    Copyright (C) 2026 Benjamin Larsson

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Kingspan/Watchman Plus (Niveau) oil tank monitor, older PWM probe sensor.

An older (~2004) probe/pole-based oil tank level sensor. Distinct from the
newer ultrasonic "Watchman Sonic" / "Watchman Sonic Advanced" already
supported by oil_watchman.c / oil_watchman_advanced.c -- this one displays
(and transmits) a single digit 0-9 or "F" (tank full), not a depth in cm.
Manual: https://www.commercialfuelsolutions.co.uk/downloads/manuals/oil_watchman.pdf

OOK PWM, raw chip width ~800 us: a "1" bit is 4 chips (~3300 us total), a
"0" bit is 5 chips (~4100 us total).

64 bit message layout (bit offsets relative to end of preamble match):

    offset  bits  field
    ------  ----  -----
     0       8    ID byte 1
     8       2    stuffing marker, always "10"
    10       8    ID byte 2
    18       2    stuffing marker, always "10"
    20       8    ID byte 3
    28       2    stuffing marker, always "10"
    30       4    level (LSB-first: bit weights 1,2,4,8)
    34       3    unknown
    37       1    battery-low
    38       2    stuffing marker, always "10"
    40       4    "complement" nibble
    44       7    tail

- Device ID: reverse the entire 24 raw ID bits then split into 8 octal digits (0-7 only)
- Level: 0-9 confirmed, value 10 = "F" (tank full), 11-15 rejected as invalid
- Battery low: confirmed by diffing real captures
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class WatchmanPlus(OOKPWMDecoder):
    """Kingspan/Watchman Plus (Niveau) oil tank monitor.

    OOK_PULSE_PWM, short=3299 us (0-bit), long=4107 us (1-bit), reset=5000 us.
    Frame: 13-bit preamble (≈12 high + 1 low) followed by 64 bits of payload.
    Payload contains 2-bit stuffing markers ("10") after every 8-bit ID/data group.
    Validation: all four stuffing pairs must equal (1,0); level must be 0–10.
    No whole-message checksum.
    Fields:
      id          – 8-octal-digit serial (24-bit ID bit-reversed, formatted octal)
      level       – "0"–"9" or "F" (full = 10)
      battery_ok  – bool (inverted battery-low bit)
    """
    name = "Watchman-Plus"
    short_us = 3299.0
    long_us = 4107.0
    reset_us = 5000.0
    n_bits = 77  # 13 preamble + 64 payload

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 64:
            return None

        # Determine payload start offset.
        # If full 77-bit frame (preamble present), skip first 13 bits.
        offset = 13 if len(bits) >= 77 else 0
        p = offset

        if len(bits) < p + 51:
            return None

        # Validate all four 2-bit stuffing markers (must be 1 then 0).
        for stuffing_bit in (p + 8, p + 18, p + 28, p + 38):
            if bits[stuffing_bit] != 1 or bits[stuffing_bit + 1] != 0:
                return None

        # Extract 24-bit ID from three data bytes, skipping stuffing bits.
        id_b1 = bits_to_int(bits[p + 0:  p + 8])
        id_b2 = bits_to_int(bits[p + 10: p + 18])
        id_b3 = bits_to_int(bits[p + 20: p + 28])
        raw_id = (id_b1 << 16) | (id_b2 << 8) | id_b3

        # Reverse all 24 bits then format as 8-digit octal serial.
        rev_id = int(f"{raw_id:024b}"[::-1], 2)
        serial = f"{rev_id:08o}"

        # Level: 4 bits LSB-first starting at payload offset 30.
        level_bits = bits[p + 30: p + 34]
        level_val = bits_to_int(level_bits[::-1])  # reverse for LSB-first
        if level_val > 10:
            return None
        level_str = "F" if level_val == 10 else str(level_val)

        # Battery-low flag at payload offset 37.
        battery_low = bool(bits[p + 37])

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": serial,
            "level": level_str,
            "battery_ok": not battery_low,
        })


__all__ = ["WatchmanPlus"]
