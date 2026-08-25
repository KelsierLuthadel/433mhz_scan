"""Yale HSA (Home Security Alarm) protocol.

Copyright (C) 2022 Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Yale HSA (Home Security Alarm) protocol.

Yale HSA Alarms, YES-Alarmkit:
- Yale HSA6010 Door/Window Contact
- Yale HSA6080 Keypad
- Yale HSA6020 Motion PIR
- Yale HSA6060 Remote Keyfob

A message is made up of 6 packets and then repeats.
Packets are 13 bits, start with 0x5 and a end-of-message flag, then 8 bit data.

Actually data should be in the gaps, which are tighter timings of 368 / 978 us.

The 6 packets combined decode as

Data Layout:

    ID:16h TYPE:8h STATE:8b EVENT:8h CHK:8h

Or perhaps?

    ID:16h TYPE:12h STATE:8b EVENT:4h CHK:8h

The checksum is just remainder of adding the 5 messages bytes, i.e. adding 6 bytes checks to zero.

Guessed data so far:
- Sensor types: ac1, ad1: window sensor, 153: PIR
- Events 1: trigger, 3: binding, 4: tamper
- State: Could be battery?

Data table:
- W/D: Contact opened:              stype: ac state: 1 0 event: 01
- W/D: Tamper button closed/off:    stype: ac state: 1 0 event: 04
- W/D: Tamper button released/on:   stype: ac state: 1 2 event: 04
- W/D: Binding button pressed:      stype: ac state: 1 2 event: 03
- W/D: Low battery:                 stype: ac state: 1 8 event: 04
- PIR:  Binding Button:             stype: 15 state: 3 0 event: 03
- PIR:  Tamper button closed/off:   stype: 15 state: 3 0 event: 04
- PIR:  Tamper button released/on:  stype: 15 state: 3 2 event: 04
- PIR:  Movement trigger:           stype: 15 state: 3 0 event: 01
- PIR:  Low battery:                stype: 15 state: 3 2 event: 01

Get Raw data with:

    rtl_433 -R 0 -X 'n=name,m=OOK_PWM,s=850,l=1460,y=5380,r=1500' ~/Desktop/Yale-6010.ook
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class YaleHSA(RawDecoder):
    """Yale Home Security Alarm sensor (OOK_PULSE_PWM, 850/1460 µs).

    6 packets of 13 bits each; multi-packet collection requires higher-level
    state machine not available in single-burst RawDecoder.decode().
    """

    name = "Yale-HSA"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["YaleHSA"]
