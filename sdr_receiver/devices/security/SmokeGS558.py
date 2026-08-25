"""Wireless Smoke & Heat Detector.

Copyright (C) 2017 Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Wireless Smoke & Heat Detector.

Ningbo Siterwell Electronics GS 558 Sw. V05 Ver. 1.3 on 433.885MHz
VisorTech RWM-460.f Sw. V05, distributed by PEARL, seen on 433.674MHz

A short wakeup pulse followed by a wide gap (11764 us gap), followed by 24 data
pulses and 2 short stop pulses (in a single bit width). This is repeated 8 times
with the next wakeup directly following the preceding stop pulses.

Bit width is 1731 us with
Short pulse: -___ 436 us pulse + 1299 us gap
Long pulse: ---_ 1202 us pulse + 526 us gap
Stop pulse: -_-_ 434us pulse + 434us gap + 434us pulse + 434us gap

= 2300 baud pulse width / 578 baud bit width

24 bits (6 nibbles):
- first 5 bits are unit number with bits reversed
- next 15(?) bits are group id, likely also reversed
- last 4 bits are always 0x3 (maybe hardware/protocol version)

Decoding will reverse the whole packet.
Short pulses are 0, long pulses 1, need to invert the demod output.

Each device has it's own group id and unit number as well as a shared/learned group id and unit number.
In learn mode the primary will offer it's group id and the next unit number.
The secondary device acknowledges pairing with 16 0x555555 packets and copies the offered shared group id and unit number.
The primary device then increases it's unit number.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SmokeGS558(OOKPWMDecoder):
    """Wireless smoke/heat detector GS 558 (OOK_PULSE_PWM, 436/1202 µs, 24 bits)."""

    name      = "Smoke-GS558"
    short_us  = 436.0
    long_us   = 1202.0
    reset_us  = 14117.0
    n_bits    = 24
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 24:
            return None
        # Invert then swap byte order (C reverses the 3-byte array)
        b = [x ^ 1 for x in bits[:24]]
        inv_b0 = bits_to_int(b[0:8])
        inv_b1 = bits_to_int(b[8:16])
        inv_b2 = bits_to_int(b[16:24])
        # reversed_byte[0] = inv_b2, [1] = inv_b1, [2] = inv_b0
        rev0, rev1, rev2 = inv_b2, inv_b1, inv_b0
        version  = (rev2 >> 4) & 0x0F
        if version != 3:
            return None
        unit     = rev0 & 0x1F
        group_id = ((rev2 & 0x0F) << 11) | (rev1 << 3) | (rev0 >> 5)
        if group_id == 0 or group_id == 0x7FFF:
            return None
        code = (inv_b0 << 16) | (inv_b1 << 8) | inv_b2
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":   group_id,
            "unit": unit,
            "code": f"{code:06X}",
        })


__all__ = ["SmokeGS558"]
