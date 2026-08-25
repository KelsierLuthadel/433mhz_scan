"""Nidec - Car Remote.

Copyright (C) 2024 Ethan Halsall

Nidec - Car Remote (313 MHz).

Manufacturer: Nidec

Supported Models:
- OUCG8D-344H-A (OEM for Honda)

The transmitter uses a rolling code message.

Button operation:
The unlock, lock buttons can be pressed once to transmit a single message.
The trunk, panic buttons will transmit the same code on a short press.
The trunk, panic buttons will transmit the unique code on a long press.
The panic button will repeat the panic code as long as it is held.

Data layout:

Bytes are inverted.

The decoder will match on the last 64 bits of the preamble: 0xfffffff0

    SSSS IIIIII 5b CCCC

- S: 16 bit sequence (plain rolling counter) that increments on each code transmitted
- I: 24 bit remote ID
- 5: 4 bit constant 0x5
- b: 4 bit button code
- C: 16 bit security/rolling-code field

On real captures this last field is almost always truncated: the demod cuts the
frame short before all 16 bits arrive. `security_bits` reports how many of the
16 bits were actually captured.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class NidecCarRemote(RawDecoder):
    """Nidec Car Remote  313.8 MHz, FSK PWM, 128-bit frame.

    Stub: preamble is 0xFFFFFFFF followed by 0xFFFFFFF0 (64 bits of marker).
    After the preamble: seq(16) | id(24) | const_0x5(4) | button(4) |
    security(16).  Valid button codes: 0x3=Lock, 0x4=Unlock, 0x5=Trunk/Panic,
    0x6=Panic Long, 0xF=Trunk Long.  Device is disabled in rtl_433.
    """
    name = "Nidec Car Remote"
    # FSK_PULSE_PWM: short=250 µs, long=500 µs, reset=1000 µs

    BUTTONS: dict[int, str] = {
        0x3: "Lock", 0x4: "Unlock", 0x5: "Trunk/Panic Short",
        0x6: "Panic Long", 0xF: "Trunk Long",
    }

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK demodulation is not supported by the OOK base classes.
        return None


__all__ = ["NidecCarRemote"]
