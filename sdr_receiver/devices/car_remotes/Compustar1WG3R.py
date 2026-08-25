"""Compustar 1WG3R - Car Remote.

Copyright (C) 2024 Ethan Halsall

Compustar 1WG3R - Car Remote.

Manufacturer: Compustar

Supported Models:
- 1WG3R-SH, 1WAMR-1900

The transmitter uses a fixed code message with 4 buttons.
Panic: Press and hold the lock button for 3 seconds.
Long Press: Hold the button combination down for 2.5 seconds.
Secondary mode: Press and hold the unlock and trunk buttons simultaneously for 2.5 seconds.

Data layout:

    IIII x bbbbbbbb iiiiiiii z

where I is 16-bit remote ID, x is 3-bit unknown (always 111),
i is 8-bit inverted button code, b is 8-bit button code,
z is 1-bit unknown (always 0).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Compustar1WG3R(OOKPWMDecoder):
    """Compustar 1WG3R Car Remote  OOK PWM, 36 bits.

    Integrity is verified by checking that the 8-bit button field equals the
    bitwise inverse of the following 8-bit inverted-button field.
    """
    name     = "Compustar 1WG3R Car Remote"
    short_us = 708.0
    long_us  = 1076.0
    reset_us = 1532.0
    n_bits   = 36

    BUTTONS: dict[int, str] = {
        0x01: "Start",  0x02: "Stop",  0x04: "Lock",  0x08: "Unlock",
        0x10: "Trunk",  0x20: "Panic", 0x40: "Aux1",  0x80: "Aux2",
    }

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        bits = bits[:36]

        # Bits 16-18 must all be 1; bit 35 must be 0
        if bits[16] != 1 or bits[17] != 1 or bits[18] != 1:
            return None
        if bits[35] != 0:
            return None

        remote_id   = bits_to_int(bits[0:16])
        button      = bits_to_int(bits[19:27])
        button_inv  = bits_to_int(bits[27:35])

        # Integrity: (~button_inv & 0xFF) == button
        if ((~button_inv) & 0xFF) != button:
            return None

        if remote_id in (0x0000, 0xFFFF):
            return None

        button_name = self.BUTTONS.get(button, f"0x{button:02X}")
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"0x{remote_id:04X}",
            "button_code": button,
            "button": button_name,
        })


__all__ = ["Compustar1WG3R"]
