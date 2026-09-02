"""BMW key fob presence detector (433.92 MHz OOK/ASK).

Detects the characteristic short-chip (~115 us) preamble of BMW key fob
transmissions. Does not attempt to decode the rolling code payload.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse

_CHIP_US   = 115.0
_TOL       = 0.50
_CHIP_MIN  = _CHIP_US * (1 - _TOL)          # ~57 us
_CHIP2_MAX = _CHIP_US * 2 * (1 + _TOL)      # ~345 us
_MIN_VALID = 6


class BmwKeyFob(RawDecoder):
    """BMW key fob button-press detector.

    BMW key fobs use OOK/ASK with Manchester encoding and a proprietary
    rolling code. This decoder identifies the preamble by its short chip
    rate (~115 us) and reports a button-press event without decoding the
    encrypted payload.
    """
    name = "BMW-KeyFob"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        if len(pulses) < _MIN_VALID:
            return None

        valid = sum(
            1 for p in pulses
            if _CHIP_MIN <= p.pulse_us <= _CHIP2_MAX
        )
        if valid < _MIN_VALID:
            return None

        return DecodedPacket.from_fields(
            self.name, freq_hz,
            {"event": "button_press", "pulses": len(pulses)},
        )


__all__ = ["BmwKeyFob"]
