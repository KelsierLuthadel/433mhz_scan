"""Dickert MAHS433-01 remote control.

Copyright (C) 2024 daubsi

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Dickert MAHS433-01 remote control.

The Dickert MAHS433-01 remote contains a user-accessible bank of 10 dip switches labeled "1" to "10" and
each tristate dip switch can be set to one of three positions. These positions are labeled as "-" (down),
"0" (half-way up), and "+" (up). Based on the position of these switches, 59,049 (3^10) unique codes are
possible. There seems to be a model of this device "MAHS433-01" that has one button to trigger a repeating
signal for the duration it is held, and there may be a "MAHS433-04" device with 4 buttons.

There's some photos and documentation on the Dickert Electronic site: https://dickert.com/de/mahs433-01-02004600.html

Note that Cardin S466-TX2 (cardin.c) also decodes a bank of tri-state DIP switches to a "dipswitch" string,
the same key name is reused here for consistency.

The signal itself is a bit unusual. Logical bits each seem to be encoded over three symbols. A logical "1" is
encoded as "001" and a logical "0" is encoded as "011" which, although it looks like typical PWM, has each bit
encoding starting with a ASK/OOK gap, then ending with the PWM pulse. The start of the signal is a single "1"
pulse symbol.

After decoding, there are 36 logical bits. The first 20 are 10 sets of 2 bits encoding the state of the 10
tristate dip switches. A "-" state is "00", a "0" state is "01" and a "+" state is "11". "10" is never observed
and seems to be invalid. The remaining 16 bits comprise a factory code of 8 more trinary symbols, which so far
has been observed identical (0x5515) across multiple devices from the same batch.

Please see more details on https://github.com/merbanan/rtl_433/issues/2983
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class DickertMAHS(OOKPWMDecoder):
    """Dickert MAHS433-01 gate remote.

    OOK_PULSE_PWM, short=362 µs, long=770 µs, reset=12000 µs.
    36 bits: 10 DIP switches (2 bits each = 20 bits) + factory code (16 bits).
    DIP encoding: 0b00 = '-', 0b01 = '0', 0b11 = '+'.  No checksum.
    """
    name     = "Dickert-MAHS433"
    short_us = 362.0
    long_us  = 770.0
    reset_us = 12000.0
    n_bits   = 36

    _DIP_MAP: dict[int, str] = {0b00: "-", 0b01: "0", 0b11: "+"}

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        switches = ""
        for i in range(0, 20, 2):
            pair = bits_to_int(bits[i : i + 2])
            switches += self._DIP_MAP.get(pair, "?")
        factory = bits_to_int(bits[20:36])
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "dip_switches": switches,
            "factory_code": f"{factory:04x}",
        })


__all__ = ["DickertMAHS"]
