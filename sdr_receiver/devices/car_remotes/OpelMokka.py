"""Opel Mokka Car Key.

Copyright (C) 2026 Vidar Madsen

Opel Mokka Car Key  FSK Manchester, 268-bit double frame.

A transponder decoder for Opel Mokka vehicle keys, likely compatible with
HITAG AES 4A NCF29A1M type devices. The decoder extracts key identification
and event type from transmissions structured as: start bit, 11-bit key ID,
5-bit packet type, 64-bit encrypted payload, and end bit. The payload is
transmitted redundantly for verification. Lock/unlock events both report
type 26, while periodic proximity signals use type 3. The encrypted payload
itself is not decrypted by this decoder.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class OpelMokka(RawDecoder):
    """Opel Mokka Car Key  FSK Manchester, 268-bit double frame.

    Stub: the 268-bit frame consists of an 88-bit zero preamble followed by
    the payload twice for redundancy validation.  Payload fields (starting at
    bit 90): key_id(11) | event_type(5) | encrypted(64) | end(1).
    The two copies are compared; a mismatch rejects the frame.
    """
    name = "Opel Mokka Car Key"
    # FSK_PULSE_MANCHESTER_ZEROBIT: short=100 µs, long=100 µs, reset=1000 µs

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        # FSK demodulation is not supported by the OOK base classes.
        return None


__all__ = ["OpelMokka"]
