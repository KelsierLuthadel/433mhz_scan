"""Security+ 1.0 rolling code.

Copyright (C) 2020 Peter Shipley <peter.shipley@gmail.com>
Based on code by Clayton Smith https://github.com/argilo/secplus

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Security+ 1.0 rolling code.

This decoder has an internal state that may change between invocations and influence the output.
The Security+ 1.0 protocol transmits two packets per button press; the first half is cached until the second arrives.

This decoder depends on wall clock time and exact timing might influence the output.
The cache expires after 800ms to avoid combining unrelated transmissions.

Freq 310, 315 and 390 MHz.

Security+ 1.0 is described in US patent application US6980655B2
https://patents.google.com/patent/US6980655B2/
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SecplusV1(RawDecoder):
    """Chamberlain / LiftMaster Security+ v1.0 (OOK_PULSE_PCM, 500 µs chip).

    Two-packet trinary-encoded rolling code (84 bits each, 800 ms window).
    Full implementation requires inter-packet state cache.
    """

    name = "Secplus-V1"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["SecplusV1"]
