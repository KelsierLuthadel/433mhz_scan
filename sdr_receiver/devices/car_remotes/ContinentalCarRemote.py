"""Continental - Car Remote.

Copyright (C) 2024 Ethan Halsall

Continental - Car Remote (313 MHz).

Manufacturer: Continental

Supported Models:
- 72147-SNA-A01 (FCC ID KR5V2X) (OEM for Honda)

The transmitter uses a rolling code with an unencrypted sequence number.

Button operation:
The unlock, lock buttons can be pressed once to transmit a single message.
The trunk, panic buttons will transmit the same code on a short press.
The trunk, panic buttons will transmit the unique code on a long press.
The panic button will repeat the panic code as long as it is held.

Data layout:
The decoder will match on the last 20 bits of the preamble: 0xf0f06.

    PPPPP IIIIIIII UU bbbb U IIIII EEEEEEEE CC

- P: 20 bit preamble (following a longer wakeup sequence)
- I: 32 bit remote ID
- U: 8 bit unknown
- b: 4 bit button code
- U: 4 bit unknown
- E: 32 bit encrypted code
- C: 8 XOR of entire payload
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ContinentalCarRemote(RawDecoder):
    """Continental KR5V2X Car Remote  313.8 MHz, FSK Manchester.

    Stub: full decoding requires FSK demodulation.  The preamble pattern is
    0xF0, 0xF0, 0x60 (20 bits).  After the preamble, a 14-byte payload
    carries: id(32) | pad(8) | button(4) | pad(4) | seq(24) | encrypted(32) |
    xor_cksum(8).  XOR of all 14 payload bytes must equal zero.
    """
    name = "Continental KR5V2X Car Remote"
    # FSK_PULSE_MANCHESTER_ZEROBIT: short=100 µs, long=200 µs, reset=1500 µs

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK demodulation is not supported by the OOK base classes.
        return None


__all__ = ["ContinentalCarRemote"]
