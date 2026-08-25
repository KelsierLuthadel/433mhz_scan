"""Decoder for Visonic Powercode devices. Tested with an MCT-302.

Copyright (C) 2020 Maxwell Lock

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

The device uses OOK PWM encoding, short pulse 400us long pulse 800us, and repeats 6 times.
You can use a flex decoder -X 'n=visonic_powercode,m=OOK_PWM,s=400,l=800,r=5000,g=900,t=160,y=0'

Powercode packet structure is 37 bits. 4 examples follow:

              s addr                       data     cksm
              1 01101111 01000111 01110000 10001100 1001 - magnet near, case open
              1 01101111 01000111 01110000 11001100 1101 - magnet away, case open
              1 01101111 01000111 01110000 00001100 0001 - magnet near, case closed
              1 01101111 01000111 01110000 01001100 0101 - magnet away, case closed
              | |                        | |||||||| |  |
     StartBit_/ /                        / |||||||| \__\_checksum, XOR of preceding nibbles
     DeviceID__/________________________/  ||||||||
                                           ||||||||
                                    Tamper_/||||||\_Repeater
                                      Alarm_/||||\_Spidernet
                                     Battery_/||\_Supervise
                                         Else_/\_Restore

1 bit start bit
3 byte(24 bit) device ID
1 byte data
1 nibble (4 bit) checksum

Checksum is a londitudinal redundancy check of the 4 bytes containing the device ID and data.
Bytes are split into nibbles. 1st bit of each nibble is XORed and result is 1st bit of checksum,
then the same for the 2nd, 3rd and 4th bits.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class VisonicPowercode(OOKPWMDecoder):
    """Visonic Powercode wireless security sensor (OOK_PULSE_PWM, 400/800 µs, 37 bits).

    Layout: 1 start + 24-bit ID + 8-bit data + 4-bit LRC checksum.
    LRC: XOR all 5 bytes, fold nibbles  (lrc>>4)^(lrc&0xF) must be 0.
    """

    name      = "Visonic-Powercode"
    short_us  = 400.0
    long_us   = 800.0
    reset_us  = 5000.0
    n_bits    = 37
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 37:
            return None
        if bits[0] != 1:       # start bit must be 1
            return None
        payload = bits[1:37]   # 36 bits: 24 ID + 8 data + 4 checksum
        msg = [bits_to_int(payload[i * 8 : i * 8 + 8]) for i in range(3)]
        msg.append(bits_to_int(payload[24:32]))          # data byte
        msg.append(bits_to_int(payload[32:36]) << 4)     # 4-bit LRC in upper nibble
        if all(m == 0 for m in msg[:4]):
            return None
        lrc = 0
        for m in msg:
            lrc ^= m
        if (lrc >> 4) ^ (lrc & 0xF) != 0:
            return None
        device_id = (msg[0] << 16) | (msg[1] << 8) | msg[2]
        d = msg[3]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         f"{device_id:06X}",
            "tamper":     int(bool(d & 0x80)),
            "alarm":      int(bool(d & 0x40)),
            "battery_ok": int(not bool(d & 0x20)),
            "else":       int(bool(d & 0x10)),
            "restore":    int(bool(d & 0x08)),
            "supervised": int(bool(d & 0x04)),
            "spidernet":  int(bool(d & 0x02)),
            "repeater":   int(bool(d & 0x01)),
            "mic":        "CHECKSUM",
        })


__all__ = ["VisonicPowercode"]
