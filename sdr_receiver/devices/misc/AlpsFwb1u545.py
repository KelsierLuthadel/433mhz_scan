"""Alps FWB1U545 - Car Remote.

Copyright (C) 2024 Ethan Halsall

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Alps FWB1U545 - Car Remote.

Manufacturer:
- Alps Electric

Supported Models:
- FWB1U545, (FCC ID CWTWB1U545) (OEM for Honda)

Data structure:

The transmitter uses a fixed code an unencrypted sequence number.

Button operation:
This transmitter has up to 4 buttons which can be pressed once to transmit a single message.

Data layout:

Data is little endian

    PP IIIIIIII bbbbbbbb bbbbbbbb SSSS CC

- P: 8 bit preamble
- I: 32 bit ID
- b: 8 bit button code
- b: 8 bit button code (copy)
- S: 16 bit sequence
- C: 4 bit unknown, maybe checksum or crc

Format string:

    PREAMBLE: bbbbbbbb ID: hhhhhhhh BUTTON: bbbbbbbb BUTTON_XOR: bbbbbbbb SEQUENCE: hhhh UNKNOWN: bbbb
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AlpsFwb1u545(RawDecoder):
    """Alps FWB1U545 Car Remote  FSK Manchester, 76 bits."""
    name = "Alps-FWB1U545"

    def decode(self, pulses, freq_hz):
        return None  # FSK not supported in OOK pipeline


__all__ = ["AlpsFwb1u545"]
