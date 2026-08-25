"""Auriol HG04641A temperature station sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _sign16_top12
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AuriolHG04641A(OOKPPMDecoder):
    """Auriol HG04641A temperature station sensor."""
    name     = "Auriol-HG04641A"
    short_us = 980.0
    long_us  = 1_976.0
    reset_us = 5_000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        b    = [bits_to_int(bits[i:i + 8]) for i in range(0, 32, 8)]  # b[0..3]
        b4hi = bits_to_int(bits[32:36])  # upper nibble = n[8]

        # 9 nibbles
        n = [
            b[0] >> 4, b[0] & 0xF,
            b[1] >> 4, b[1] & 0xF,
            b[2] >> 4,              # n[4] = flags
            b[2] & 0xF,             # n[5] = temp[11:8]
            b[3] >> 4, b[3] & 0xF, # n[6..7] = temp[7:0]
            b4hi,                   # n[8] = checksum
        ]

        # Nibble-sum checksum
        if sum(n[:8]) % 16 != n[8]:
            return None

        device_id   = (b[0] << 8) | b[1]
        battery_low = (n[4] >> 3) & 1

        # 12-bit temp from n[5:8], top-aligned
        t16    = (n[5] << 12) | (n[6] << 8) | (n[7] << 4)
        temp_c = _sign16_top12(t16) * 0.1

        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["AuriolHG04641A"]
