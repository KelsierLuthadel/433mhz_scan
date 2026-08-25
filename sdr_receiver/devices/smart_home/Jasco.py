"""Jasco/GE Choice Alert Wireless Device Decoder.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Jasco/GE Choice Alert Wireless Device Decoder.

- Frequency: 318.01 MHz

Manchester PCM with a de-sync preamble of 0xFC0C (11111100000011000).

Packets are 32 bit, 24 bit data and 8 bit XOR checksum.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Jasco(OOKPCMDecoder):
    """Jasco / GE Choice-Alert door and window sensor.

    OOK_PULSE_PCM, chip=250 µs, reset=1800 µs.
    Preamble: 0xFC 0x0C (16 PCM bits), then Manchester-encoded 32-bit payload.
    XOR of all 4 decoded bytes must be 0x00.
    Fields: id[16] | status[8] | checksum[8].
    Sensor closed: (status & 0xEF) == 0xEF.
    """
    name     = "Jasco-Security"
    chip_us  = 250.0
    reset_us = 1800.0
    n_bits   = 80   # preamble 16 + Manchester 64 PCM chips

    _PREAMBLE = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0]

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        n = len(bits)
        if n < 80:
            return None
        # locate 0xFC0C preamble
        start = -1
        for i in range(n - 16):
            if bits[i : i + 16] == self._PREAMBLE:
                start = i + 16
                break
        if start < 0 or start + 64 > n:
            return None
        # Manchester decode: falling edge=1, rising edge=0
        decoded: list[int] = []
        i = start
        while i + 1 < n and len(decoded) < 32:
            a, bb = bits[i], bits[i + 1]
            if a == 1 and bb == 0:
                decoded.append(1)
            elif a == 0 and bb == 1:
                decoded.append(0)
            else:
                return None
            i += 2
        if len(decoded) < 32:
            return None
        b = [bits_to_int(decoded[i : i + 8]) for i in range(0, 32, 8)]
        if (b[0] ^ b[1] ^ b[2] ^ b[3]) != 0:
            return None
        sensor_id = (b[0] << 8) | b[1]
        closed    = (b[2] & 0xEF) == 0xEF
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":     sensor_id,
            "closed": int(closed),
            "mic":    "XOR",
        })


__all__ = ["Jasco"]
