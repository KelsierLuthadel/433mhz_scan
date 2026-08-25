"""Ford Car Key.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Ford Car Key.

Identifies event, but does not attempt to decrypt rolling code.
Note: this used to have a broken PWM decoding, but is now proper DMC.
The output changed and the fields are very likely not as intended.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class FordRemote(RawDecoder):
    """Ford Car Key  OOK DMC (differential Manchester), multi-row protocol.

    Stub: the protocol uses OOK_PULSE_DMC with a three-row preamble
    ({1-bit}, {9-bit 0x00}, {1-bit}) followed by a 78+ bit payload.
    Fields: id(24) from bytes 0-2, code(8) from byte 7.
    Rolling code is not decrypted.  Device is disabled in rtl_433.
    """
    name = "Ford Car Key"
    # OOK_PULSE_DMC: short=250 µs, long=500 µs, reset=4000 µs

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # DMC with multi-row framing is not yet supported.
        return None


__all__ = ["FordRemote"]
