"""Universal Reversible 24V Fan Controller remote decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class UniversalFanCtrl(OOKPWMDecoder):
    """Universal Reversible 24V Fan Controller remote.

    OOK_PULSE_PWM, short=256 µs, long=756 µs, reset=8800 µs.
    33 bits: addr[20] | button[5] | counter[3] | checksum[4] | fixed_1.
    Checksum: XOR bytes 0-3, fold nibbles, result == 0xA.
    """
    name     = "UniversalFanCtrl"
    short_us = 256.0
    long_us  = 756.0
    reset_us = 8800.0
    n_bits   = 33

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 33:
            return None
        if bits[32] != 1:
            return None
        b = [bits_to_int(bits[i : i + 8]) for i in range(0, 32, 8)]
        xval = b[0] ^ b[1] ^ b[2] ^ b[3]
        fold = (xval ^ (xval >> 4)) & 0xF
        if fold != 0xA:
            return None
        addr    = bits_to_int(bits[0:20])
        button  = bits_to_int(bits[20:25])
        counter = bits_to_int(bits[25:28])
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":      addr,
            "button":  button,
            "counter": counter,
        })


__all__ = ["UniversalFanCtrl"]
