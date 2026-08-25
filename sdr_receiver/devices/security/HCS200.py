"""Microchip HCS200/HCS300 KeeLoq Code Hopping Encoder based remotes.

Copyright (C) 2019, 667bdrm

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Microchip HCS200/HCS300 KeeLoq Code Hopping Encoder based remotes.

66 bits transmitted, LSB first.

|  0-31 | Encrypted Portion
| 32-59 | Serial Number
| 60-63 | Button Status (S3, S0, S1, S2)
|  64   | Battery Low
|  65   | Fixed 1

Note that the button bits are (MSB/first sent to LSB) S3, S0, S1, S2.
Hardware buttons might map to combinations of these bits.

- Datasheet HCS200: http://ww1.microchip.com/downloads/en/devicedoc/40138c.pdf
- Datasheet HCS300: http://ww1.microchip.com/downloads/en/devicedoc/21137g.pdf

The warm-up of 12 short pulses is followed by a long 4400 us gap.
There are two packets with a 17500 us gap.

rtl_433 -R 0 -X 'n=hcs200,m=OOK_PWM,s=370,l=772,r=9000,g=1500,t=152'
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from .._helpers import _bits_to_bytes_lsb
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HCS200(OOKPWMDecoder):
    """Microchip HCS200/HCS300 KeeLoq rolling-code remote (OOK_PULSE_PWM).

    370/772 µs, 66 bits LSB-first: 32 encrypted + 28 serial +
    4 buttons (S3 S0 S1 S2) + 1 battery_low + 1 fixed.
    Preceded by 12-bit 0xFFF preamble (skipped).
    """

    name      = "Microchip-HCS200"
    short_us  = 370.0
    long_us   = 772.0
    reset_us  = 9000.0
    n_bits    = 78   # 12 preamble + 66 data
    tolerance = 0.45

    def _extract(self, bits: list[int]) -> DecodedPacket | None:
        raw = _bits_to_bytes_lsb(bits[:64])   # 8 bytes, LSB-first assembled
        if all(b == 0xFF for b in raw):
            return None
        enc    = (raw[0] << 24) | (raw[1] << 16) | (raw[2] << 8) | raw[3]
        serial = raw[4] | (raw[5] << 8) | (raw[6] << 16) | ((raw[7] & 0x0F) << 24)
        btn_ny = (raw[7] >> 4) & 0xF          # S3 S0 S1 S2 at bits 4-7 of raw[7]
        s3 = (btn_ny >> 3) & 1
        s0 = (btn_ny >> 2) & 1
        s1 = (btn_ny >> 1) & 1
        s2 = (btn_ny >> 0) & 1
        button      = (s0 << 3) | (s1 << 2) | (s2 << 1) | s3
        battery_low = bool(bits[64]) if len(bits) > 64 else False
        learn       = button == 0x0F
        return (serial, button, learn, battery_low, enc)

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Skip leading preamble 1s
        start = 0
        while start < len(bits) - 66 and bits[start] == 1 and start < 16:
            start += 1
        working = bits[start:]
        if len(working) < 66:
            return None
        result = self._extract(working)
        if result is None:
            return None
        serial, button, learn, battery_low, enc = result
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         f"{serial:07X}",
            "button":     button,
            "learn":      int(learn),
            "battery_ok": int(not battery_low),
            "encrypted":  f"{enc:08X}",
        })


__all__ = ["HCS200"]
