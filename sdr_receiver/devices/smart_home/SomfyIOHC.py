"""Somfy io-homecontrol devices.

Copyright (C) 2021 Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Somfy io-homecontrol devices.

E.g. Velux remote controller KI 313.

    rtl_433 -c 0 -R 0 -g 40 -X "n=uart,m=FSK_PCM,s=26,l=26,r=300,preamble={24}0x5555ff,decode_uart" -f 868.89M

Protocol description:

- Preamble is 55..55.
- The message, including the sync word is UART encoded, 8 data bits equal 10 packet bits.
- 16 bit sync word of ff33, UART encoded: 0 ff 1 0 cc 1 = 7fd99.
- 4+4 bit message type/length indicator byte.
- 32 bit destination address (little endian presumably).
- 32 bit source address (little endian presumably).
- n bytes variable length message payload bytes
- 16 bit MAC counter value
- 48 bit MAC value
- 16 bit CRC-16, poly 0x1021, init 0x0000, reflected.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SomfyIOHC(RawDecoder):
    """Somfy io-homecontrol (iohc) motorised blind system.

    FSK_PULSE_PCM, chip=26 µs, reset=300 µs.  UART 8N1 framing.
    Frame: ctrl[8] | flags[8] | dst[24] | src[24] | cmd[8] | data | CRC-16.
    CRC-16: poly=0x8408 (reflected 0x8005), init=0x0000 over full frame.
    Stub: FSK demodulation not supported in OOK pipeline.
    """
    name = "Somfy-IOHC"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK demodulation


__all__ = ["SomfyIOHC"]
