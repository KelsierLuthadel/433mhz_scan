"""Chamberlain CWPIRC pir sensor.

Copyright (C) 2023 Bruno OCTAU
Copyright (C) 2026 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Chamberlain CWPIRC pir sensor.
Issue #2582 open by @kuenkin

This is the webpage of the product itself: https://www.chamberlain.com/ca/cwp-wireless-motion-alert-add-on-sensor/p/CWPIRC

The pir sensor have a learn feature for pairing purpose with the base station up to 8 sensors.

Data layout :

    Byte position                00 01 02 03 04 05 06 07 08 09 10 11 12 13
        55 55 ... 55 55 55 2D D4 00 xx xx xx xx xx 01 yy yy yy yy yy CC CC

- Message 0   {48} 00 xx xx xx xx xx, always starting with 0x00
- Message 1   {48} 01 yy yy yy yy yy, always starting with 0x01
- CRC-16XModem{16} cc cc  from 00 to 11 byte

Each 40-bit message reuses the Security+ 2.0 joint-message permutation
from secplus_v2.c (a 4-bit order nibble, a 4-bit invert nibble, then 30
bits of interleaved triplets). The resulting 40-bit "fixed" value stays
constant per physical sensor while a 28-bit rolling counter changes every
transmission. Bit 5 of fixed is a low-battery flag.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ChamberlainCwpirc(RawDecoder):
    """Chamberlain CWPIRC PIR Sensor  FSK PCM, Security+ 2.0 rolling code."""
    name = "Chamberlain-CWPIRC"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["ChamberlainCwpirc"]
