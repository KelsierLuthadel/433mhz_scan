"""DSC security contact sensors.

Copyright (C) 2015 Tommy Vestermark
Copyright (C) 2015 Robert C. Terzi

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

DSC - Digital Security Controls 433 Mhz Wireless Security Contacts
doors, windows, smoke, CO2, water.

Protocol Description available in this FCC Report for FCC ID F5300NB912
https://apps.fcc.gov/eas/GetApplicationAttachment.html?id=100988

General Packet Description
- Packets are 26.5 mS long
- Packets start with 2.5 mS of constant modulation for most sensors
  Smoke/CO2/Fire sensors start with 5.6 mS of constant modulation
- The length of a bit is 500 uS, broken into two 250 uS segments.
   A logic 0 is 500 uS (2 x 250 uS) of no signal.
   A logic 1 is 250 uS of no signal followed by 250 uS of signal/keying
- Then there are 4 sync logic 1 bits.
- There is a sync/start 1 bit in between every 8 bits.
- A zero byte would be 8 x 500 uS of no signal (plus the 250 uS of
  silence for the first half of the next 1 bit) for a maximum total
  of 4,250 uS (4.25 mS) of silence.
- The last byte is a CRC with nothing after it, no stop/sync bit, so
  if there was a CRC byte of 0, the packet would wind up being short
  by 4 mS and up to 8 bits (48 bits total).
- Note the WS4945 doubles the length of those timings.

There are 48 bits in the packet including the leading 4 sync 1 bits.
This makes the packet 48 x 500 uS bits long plus the 2.5 mS preamble
for a total packet length of 26.5 ms.  (smoke will be 3.1 ms longer)

Packet Decoding

    Check intermessage start / sync bits, every 8 bits
    Byte 0   Byte 1   Byte 2   Byte 3   Byte 4   Byte 5
    vvvv         v         v         v         v
    SSSSdddd ddddSddd dddddSdd ddddddSd dddddddS cccccccc  Sync,data,crc
    01234567 89012345 67890123 45678901 23456789 01234567  Received Bit No.
    84218421 84218421 84218421 84218421 84218421 84218421  Received Bit Pos.

    SSSS         S         S         S         S           Synb bit positions
        ssss ssss ttt teeee ee eeeeee e eeeeeee  cccccccc  type
        tttt tttt yyy y1111 22 223333 4 4445555  rrrrrrrr

- Bits: 0,1,2,3,12,21,30,39 should == 1

- Status (st) = 8 bits, open, closed, tamper, repeat
- Type (ty)   = 4 bits, Sensor type, really first nybble of ESN
- ESN (e1-5)  = 20 bits, Electronic Serial Number: Sensor ID.
- CRC (cr)    = 8 bits, CRC, type/polynom to be determined

The ESN in practice is 24 bits, The type + remaining 5 nybbles.
The physical devices have all 6 digits printed in hex. Devices are enrolled
by entering or recording the 6 hex digits.

The CRC is 8 bit, reflected (lsb first), Polynomial 0xf5, Initial value 0x3d

Status bit breakout:

The status byte contains a number of bits that indicate:
-  open vs closed
- event vs heartbeat
- battery ok vs low
- tamper
- recent activity (for certain devices)

The majority of the DSC sensors use the status bits the same way.
There are some slight differences depending on who made the device.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class DSCSecurity(RawDecoder):
    """DSC wireless security contact (OOK_PULSE_RZ, 250/500 µs).

    Sync bits at positions 0-3, 12, 21, 30, 39; reflected CRC-8
    (poly=0xF5, init=0x3D, LSB-first) over 5 data bytes.
    """

    name     = "DSC-Security"
    _SYNC    = frozenset({0, 1, 2, 3, 12, 21, 30, 39})
    SHORT_US = 250.0
    LONG_US  = 500.0

    def _crc8le(self, data: bytes) -> int:
        crc = 0x3D
        for byte in data:
            for _ in range(8):
                if (crc ^ byte) & 1:
                    crc = (crc >> 1) ^ 0xAF   # reflect(0xF5)=0xAF
                else:
                    crc >>= 1
                byte >>= 1
        return crc

    def _demod(self, pulses: list["Pulse"]) -> list[int]:
        bits: list[int] = []
        half = self.SHORT_US
        tol  = half * 0.6
        for p in pulses:
            pu = getattr(p, "pulse_us", 0) or getattr(p, "length", 0) * 1e6
            gu = getattr(p, "gap_us", 0)   or getattr(p, "gap", 0) * 1e6
            if abs(pu - half) > tol:
                continue
            if abs(gu - self.LONG_US) < tol:
                bits.append(1)
            elif abs(gu - half) < tol:
                bits.append(0)
        return bits

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        bits = self._demod(pulses)
        if len(bits) < 48:
            return None
        sync_ok = all(bits[p] == 1 for p in self._SYNC if p < len(bits))
        if not sync_ok:
            return None
        data_bits = [b for i, b in enumerate(bits[:48]) if i not in self._SYNC]
        if len(data_bits) < 40:
            return None
        msg = bytes(bits_to_int(data_bits[i : i + 8]) for i in range(0, 40, 8))
        if self._crc8le(msg) != 0:
            return None
        status = msg[0]
        esn    = (msg[1] << 16) | (msg[2] << 8) | msg[3]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         f"{esn:06X}",
            "status":     status,
            "closed":     int(bool(status & 0x02)),
            "event":      int(not bool(status & 0x40)),
            "tamper":     int(not bool(status & 0x01) or bool(status & 0x10)),
            "battery_ok": int(not bool(status & 0x08)),
            "mic":        "CRC",
        })


__all__ = ["DSCSecurity"]
