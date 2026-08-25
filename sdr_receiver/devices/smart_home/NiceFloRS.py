"""Nice Flor-s / Nice One rolling-code gate/garage remote decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class NiceFloRS(OOKPWMDecoder):
    """Nice Flor-s / Nice One rolling-code gate/garage remote.

    OOK_PULSE_PWM, short=500 µs, long=1000 µs, reset=5000 µs.
    52 bits (Nice Flor-s) or 72 bits (Nice One) → 13 or 18 nibbles.
    Payload is encrypted; serial and rolling-code are returned verbatim.
    """
    name     = "Nice-FloR-S"
    short_us = 500.0
    long_us  = 1000.0
    reset_us = 5000.0
    n_bits   = 52

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        n = len(bits)
        if n < 52:
            return None
        nibs = [bits_to_int(bits[i * 4 : (i + 1) * 4]) for i in range(n // 4)]
        if len(nibs) < 13:
            return None
        button     = nibs[0] & 0xF
        retrans    = (nibs[1] ^ (nibs[0] ^ 0xF)) & 0xF
        enc_serial = (nibs[2] << 24 | nibs[7] << 20 | nibs[8] << 16
                      | nibs[9] << 12 | nibs[10] << 8 | nibs[11] << 4 | nibs[12])
        enc_code   = nibs[3] << 12 | nibs[4] << 8 | nibs[5] << 4 | nibs[6]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "button":     button,
            "enc_serial": enc_serial,
            "enc_code":   enc_code,
            "retrans":    retrans,
        })


__all__ = ["NiceFloRS"]
