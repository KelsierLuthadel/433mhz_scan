"""Vivint Door/Window Sensors (345 MHz).

Copyright (C) 2026 Benjamin Larsson <banan@ludd.ltu.se>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Vivint Door/Window Sensors (345.0 MHz).

Tested with the Vivint V-DW21R-345 door/window sensor and Vivint V-DW11-345 Door Sensor.

OOK Manchester (zerobit), 0xFFFE preamble, 96 bit (12 byte) packet. Decoded
payload (80 data bits, 10 bytes) after the preamble:

    TT CC CC FF II II II II RR RR

- T: 8 bit frame subtype: 0x7a = DW11 door/window, 0x79 = GB2 glass-break,
     0x74 = PIR2 motion, 0x72/0x73/0x76 = other sensor families,
     0xd0 = power-on/startup beacon
- C: 16 bit counter, increments every transmission
- F: 8 bit status byte. The low 2 bits are always zero; the rest (including
     bit 7, open/closed for 0x7a) are XORed with a per-device keystream,
     see below
- I: 32 bit device identifier
- R: 16 bit CRC

I is the sensor's printed TXID: split into a 12 bit and a 20 bit decimal
number, e.g. 0x0137beda -> 19, 507610 -> "0019-0507610" (label
"0019-050-7610"). Exposed as the `id` field.

Non-0xd0 subtypes use a packed 12-bit CRC:
  - CRC-16 poly 0x8050 over b[0..7] + top_nibble(b[8])  (9 bytes)
  - check12 = crc16 >> 4; stored12 = (low_nibble(b[8]) << 8) | b[9]
  - valid when check12 == stored12

0xd0 frames use standard CRC-16 poly 0x8050 over b[0..7].

See https://github.com/merbanan/rtl_433/issues/1504
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class VivintSensor(ManchesterDecoder):
    """Vivint door/window / PIR sensor (OOK_PULSE_MANCHESTER_ZEROBIT, 150 µs chip).

    Preamble 0xFFFE, 80-bit payload: subtype(8) + counter(16) + flags(8)
    + device_id(32) + CRC-16(16) [poly=0x8050].
    """

    name      = "Vivint"
    chip_us   = 150.0
    reset_us  = 300.0
    n_bits    = 96    # 16 preamble + 80 payload
    tolerance = 0.45

    _SUBTYPES = {0x7A: "DW11", 0x79: "GB2", 0x74: "PIR2", 0xD0: "beacon"}
    _PREAMBLE = [1] * 15 + [0]   # 0xFFFE

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 80:
            return None
        found = -1
        for s in range(min(32, len(bits) - 80)):
            if bits[s : s + 16] == self._PREAMBLE:
                found = s + 16
                break
        if found < 0 or found + 80 > len(bits):
            # No preamble found  try treating from bit 0 as payload
            if len(bits) < 80:
                return None
            found = 0
        payload = bits[found : found + 80]
        data    = bytes(bits_to_int(payload[i : i + 8]) for i in range(0, 80, 8))
        subtype = data[0]
        counter = (data[1] << 8) | data[2]
        flags   = data[3]
        dev_id  = (data[4] << 24) | (data[5] << 16) | (data[6] << 8) | data[7]
        # CRC check
        if subtype == 0xD0:
            crc_recv = (data[8] << 8) | data[9]
            crc_ok   = crc16(data[:8], poly=0x8050, init=0,
                             ref_in=False, ref_out=False) == crc_recv
        else:
            crc_data  = data[:8] + bytes([data[8] & 0xF0])
            crc_recv  = ((data[8] & 0x0F) << 8) | data[9]
            crc_ok    = (crc16(crc_data, poly=0x8050, init=0,
                               ref_in=False, ref_out=False) & 0xFFF) == crc_recv
        if not crc_ok:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           dev_id,
            "counter":      counter,
            "event_type":   self._SUBTYPES.get(subtype, f"0x{subtype:02X}"),
            "flags":        flags,
            "contact_open": int(bool(flags & 0x80)),
            "tamper":       int(bool(flags & 0x40)),
            "reed":         int(bool(flags & 0x20)),
            "alarm":        int(bool(flags & 0x10)),
            "battery_low":  int(bool(flags & 0x08)),
            "heartbeat":    int(bool(flags & 0x04)),
            "mic":          "CRC",
        })


__all__ = ["VivintSensor"]
