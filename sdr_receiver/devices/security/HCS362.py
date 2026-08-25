"""Microchip HCS362 KeeLoq Code Hopping Encoder based remotes.

Copyright (C) 2024 Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Microchip HCS362 KeeLoq Code Hopping Encoder based remotes.

There are two transmission modes: PWM (mode 0) and MC (mode 1).

With Extended Serial Number disabled (XSER = 0) and CRC status selected
(CTSEL = 1), 69 bits are transmitted, LSB first:

|  0-31 | 32 bit Encrypted Portion (hopping code, needs the crypt key to decode)
| 32-59 | 28 bit Serial Number
| 60-63 |  4 bit Function Code (S3, S0, S1, S2)
| 64    |  1 bit Battery Low (Low Voltage Detector Status, VLOW)
| 65-66 |  2 bit CRC (CRC0, CRC1)
| 67-68 |  2 bit Queue (QUEUE0, QUEUE1)

Note that the button bits are (MSB/first sent to LSB) S3, S0, S1, S2.
Hardware buttons might map to combinations of these bits.

The CRC is computed over the preceding 65 bits (Encrypted Portion, Serial
Number, Function Code and VLOW) per datasheet Equation 3-1, a 2-bit shift
register seeded to 0 and updated per transmitted bit Di (0 <= i <= 64):

    CRC1[i+1] = CRC0[i] ^ Di
    CRC0[i+1] = CRC0[i] ^ Di ^ CRC1[i]

This decoder assumes the encoder is configured for CRC status (CTSEL = 1,
the default); if the encoder is configured for TIME bits (CTSEL = 0)
instead, the CRC check below will always fail.

- Datasheet HCS362: https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/40189E.pdf

PWM mode:

The preamble is 12 short pulses (0xfff), followed by the 69 data bits, PWM coded
(short is 1, long is 0).

    rtl_433 -R 0 -X 'n=HCS362,m=OOK_PWM,s=200,l=400,g=550,r=900'

MC mode:

The preamble is 12 short pulses, followed by a long sync gap, then a hardcoded
start bit (logic 1) and 69 MC coded data bits, then a stop bit that
breaks the MC coding and ends the transmission.

    rtl_433 -R 0 -X 'n=HCS362,m=OOK_PCM,s=214,l=214,g=600,r=900'
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from .._helpers import _bits_to_bytes_lsb
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HCS362(OOKPWMDecoder):
    """Microchip HCS362 KeeLoq rolling-code remote (OOK_PULSE_PWM).

    200/400 µs, 69 bits LSB-first: 66 data + 2-bit CRC + 2 queue bits.
    """

    name      = "Microchip-HCS362"
    short_us  = 200.0
    long_us   = 400.0
    reset_us  = 900.0
    n_bits    = 69
    tolerance = 0.35

    @staticmethod
    def _crc2(bits: list[int]) -> int:
        crc1 = crc0 = 0
        for b in bits[:65]:
            crc1, crc0 = crc0 ^ b, crc0 ^ b ^ crc1
        return (crc1 << 1) | crc0

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 67:
            return None
        crc_calc = self._crc2(bits)
        crc_recv = (bits[66] << 1) | bits[65]
        if crc_calc != crc_recv:
            return None
        raw = _bits_to_bytes_lsb(bits[:64])
        if all(b == 0xFF for b in raw):
            return None
        enc    = (raw[0] << 24) | (raw[1] << 16) | (raw[2] << 8) | raw[3]
        serial = raw[4] | (raw[5] << 8) | (raw[6] << 16) | ((raw[7] & 0x0F) << 24)
        btn_ny = (raw[7] >> 4) & 0xF
        s3 = (btn_ny >> 3) & 1; s0 = (btn_ny >> 2) & 1
        s1 = (btn_ny >> 1) & 1; s2 = (btn_ny >> 0) & 1
        button     = (s0 << 3) | (s1 << 2) | (s2 << 1) | s3
        battery_ok = not bool(bits[64])
        repeat     = ((bits[67] << 1) | bits[68]) if len(bits) >= 69 else 0
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         f"{serial:07X}",
            "button":     button,
            "battery_ok": int(battery_ok),
            "repeat":     repeat,
            "encrypted":  f"{enc:08X}",
            "mic":        "CRC",
        })


__all__ = ["HCS362"]
