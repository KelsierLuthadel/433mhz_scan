"""Auriol 4-LD5661/4-LD5972/4-LD6313, Sempre 4-AH0423-4 temperature/rain sensors."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _sign16_top12
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Auriol4LD5661(OOKPPMDecoder):
    """Auriol 4-LD5661/4-LD5972/4-LD6313, Sempre 4-AH0423-4 temperature/rain sensors."""
    name     = "Auriol-4LD5661"
    short_us = 1_000.0
    long_us  = 2_000.0
    reset_us = 4_000.0
    n_bits   = 52

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 52:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 48, 8)]  # b[0..5]
        last4 = bits_to_int(bits[48:52])

        # Fixed-byte validation
        if b[3] != 0xF0 or (b[1] & 0x40) != 0:
            return None

        device_id  = b[0]
        battery_ok = (b[1] >> 7) & 1

        # Temperature: 12-bit signed, top-aligned in int16
        t16    = ((b[1] & 0x0F) << 12) | (b[2] << 4)
        temp_c = _sign16_top12(t16) * 0.1

        if not -50.0 <= temp_c <= 80.0:
            return None

        # Rain counter: 20-bit value across b[4], b[5], last4
        rain_raw = (b[4] << 12) | (b[5] << 4) | last4
        rain_mm  = float(rain_raw)

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
            "rain_mm":       rain_mm,
        })


__all__ = ["Auriol4LD5661"]
