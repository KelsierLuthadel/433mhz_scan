"""Generic wireless motion/alarm sensor decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GenericMotion(OOKPWMDecoder):
    """Generic wireless motion/alarm sensor (OOK_PULSE_PWM, 888/1558 µs, 20 bits).

    No checksum; code is a 5-hex-digit value.
    """

    name      = "Generic-Motion"
    short_us  = 888.0
    long_us   = 1558.0
    reset_us  = 4086.0
    n_bits    = 20
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 20:
            return None
        b0 = bits_to_int(bits[0:8])
        b1 = bits_to_int(bits[8:16])
        b2 = bits_to_int(bits[16:20]) << 4
        if (b1 == 0 and b2 == 0) or (b1 == 0xFF and b2 == 0xF0):
            return None
        code = (b0 << 12) | (b1 << 4) | (b2 >> 4)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "code": f"{code:05X}",
        })


__all__ = ["GenericMotion"]
