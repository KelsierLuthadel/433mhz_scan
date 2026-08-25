"""RojaFlex shutter and remote devices.

Copyright (c) 2021 Sebastian Hofmann <sebastian.hofmann+rtl433@posteo.de>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

RojaFlex shutter and remote devices.

- Frequency: 433.92 MHz

Data layout:

    0xaaaaaaaa d391d391 SS KKKKKK ?CDDDD TTTT CCCC

- 4 byte Preamble   : "0xaaaaaaaa"
- 4 byte Sync Word  : "9391d391"
- 1 byte Size       : "S" is always "0x08"
- 3 byte ID         : Seems to be the static ID for the Homeinstallation
- 3 byte Data       : See below
- 1 byte Token I    : It seems to be an internal message token which is used for the shutter answer.
- 1 byte Token II   : Is the sum of 3 Bytes ID + 3 Bytes Data + 1 Byte token
- 2 byte CRC-16/CMS : poly 0x8005 init 0xffff, seems optional, missing from commands via bridge P2D.

To get raw data:

    ./rtl_433 -f 433920000 -X n=RojaFlex,m=FSK_PCM,s=100,l=100,r=102400
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class RojaFlex(RawDecoder):
    """RojaFlex motorised-blind remote.

    FSK_PULSE_PCM, chip=100 µs, reset=102400 µs.
    Frame: length[8]=0x08 | id[28] | channel[4] | cmd_id[8] | cmd_val[8] |
    token[16] | CRC-16/CMS (poly=0x8005, init=0xffff).
    Stub: FSK demodulation not supported in OOK pipeline.
    """
    name = "RojaFlex"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK demodulation


__all__ = ["RojaFlex"]
