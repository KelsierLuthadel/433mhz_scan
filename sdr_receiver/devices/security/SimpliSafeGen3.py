"""SimpliSafe Gen 3 protocol.

Copyright (C) 2021 Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

SimpliSafe Gen 3 protocol.

The data is sent at 433.9MHz using FSK at 4800 baud with a preamble and sync of `aaaaaaa 930b 51de`.

Known message length/types:
- Arm: 15 01
- Disarm: 18 01
- Sensors: 16 02

Data Layout:

    LEN:8h TYP:8h ID:32h CTR:24h CMAC:32h ENCR:80h CHK:16h

Example codes:

    55555554985a8ef0b01004fa89af407800c32b888bff61098d3627bdd5d369ca1800000000
    d55555552616a3bc2c04013ea26bd01e0030cae222ffd842634d89ef7574da728600000000
    d55555552616a3bc2c04013ea26bd21e0103b1a07f861673b5d1c531fa0bcd269c00000000
    55555554985a8ef0b01004fa89af4878040ec681fe1859ced74714c7e82f349a7000000000
    55555554985a8ef0b01004fa89af4878040ec681fe1859ced74714c7e82f349a7000000000
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class SimpliSafeGen3(RawDecoder):
    """SimpliSafe Gen 3 home security system (FSK_PULSE_PCM, 4800 baud, encrypted).

    27-byte frame with CMAC and CRC-16; payload is AES-encrypted.
    Requires FSK demodulation pipeline.
    """

    name = "SimpliSafe-Gen3"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["SimpliSafeGen3"]
