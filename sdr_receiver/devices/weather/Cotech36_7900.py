"""Cotech 36-7900 rain gauge (60-bit PPM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Cotech36_7900(OOKPPMDecoder):
    """Cotech 36-7900 rain gauge (60-bit PPM)."""
    name     = "Cotech-36-7900"
    short_us = 1000.0
    long_us  = 2000.0
    reset_us = 4500.0
    n_bits   = 60

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 60:
            return None
        marker = bits_to_int(bits[0:16])
        if marker != 0xAB80:
            return None
        temp_raw = bits_to_int(bits[16:28])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c = temp_raw / 10.0
        # Reserved field (bits 28-47) must be zero
        reserved = bits_to_int(bits[28:48])
        if reserved != 0:
            return None
        rain_count = bits_to_int(bits[48:60])
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "temperature_C": round(temp_c, 1),
            "rain_count": rain_count,
        })


__all__ = ["Cotech36_7900"]
