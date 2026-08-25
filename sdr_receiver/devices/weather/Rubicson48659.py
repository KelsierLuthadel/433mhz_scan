"""Rubicson 48659 thermometer (32-bit PPM, temperature in °F)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Rubicson48659(OOKPPMDecoder):
    """Rubicson 48659 thermometer (32-bit PPM, temperature in °F)."""
    name     = "Rubicson-48659"
    short_us = 940.0
    long_us  = 1900.0
    reset_us = 4000.0
    n_bits   = 32

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 32, 8))
        chk = (b[0] + b[1] + b[2] - b[3]) & 0xFF
        if chk != 0xA6:
            return None
        device_id = b[0]
        sign      = (b[1] & 0x04) >> 2
        temp_raw  = ((b[1] & 0x03) << 8) | b[2]
        if sign:
            temp_raw = -temp_raw
        temp_f = temp_raw / 10.0
        temp_c = (temp_f - 32.0) / 1.8
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id,
            "temperature_F": round(temp_f, 1),
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["Rubicson48659"]
