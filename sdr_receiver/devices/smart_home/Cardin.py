"""Cardin S466-TX2 generic garage door remote control on 27.195 Mhz.

Copyright (C) 2018 Christian W. Zuckschwerdt <zany@triq.net>
original implementation 2015 Denis Bodor

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Cardin S466-TX2 generic garage door remote control on 27.195 Mhz.

Note: Similar to an EV1527 / SC2260, but there is a 6152 us sync pulse first, then 24 bit of 732 us / 1412 us leading-gap PWM.
Decodes to 9 tri-state DIP-switches and a 2-bit button.

Remember to set the correct freq with -f 27.195M
May be useful for other Cardin product too

- "11R"  = on-on    Right button used
- "10R"  = on-off   Right button used
- "01R"  = off-on   Right button used
- "00L?" = off-off  Left button used or right button does the same as the left
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Cardin(OOKPWMDecoder):
    """Cardin S466-TX2 gate/garage remote.

    OOK_PULSE_PWM, short=730 µs, long=1400 µs, reset=32000 µs.
    24 bits: 9 tri-state DIP switches (2 bits each) + button (6 bits).
    Valid button codes: 0x03→'11R', 0x06→'10R', 0x09→'01R', 0x0c→'00L'.
    """
    name     = "Cardin-S466"
    short_us = 730.0
    long_us  = 1400.0
    reset_us = 32000.0
    n_bits   = 24

    _BUTTONS: dict[int, str] = {
        0x03: "11R", 0x06: "10R", 0x09: "01R", 0x0c: "00L"
    }
    _SWITCH_STATES: dict[int, str] = {0b00: "-", 0b01: "o", 0b11: "+"}

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 24:
            return None
        b = [bits_to_int(bits[i : i + 8]) for i in range(0, 24, 8)]
        btn_code = b[2] & 0x3F
        if btn_code not in self._BUTTONS:
            return None
        raw16 = (b[0] << 8) | b[1]
        dips  = ""
        for shift in (14, 12, 10, 8, 6, 4, 2, 0):
            pair = (raw16 >> shift) & 0x3
            dips += self._SWITCH_STATES.get(pair, "?")
        pair9 = (b[2] >> 6) & 0x3
        dips += self._SWITCH_STATES.get(pair9, "?")
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "button":      self._BUTTONS[btn_code],
            "dip_switches": dips,
        })


__all__ = ["Cardin"]
