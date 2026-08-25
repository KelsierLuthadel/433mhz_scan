"""Acurite 896 Rain Gauge."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AcuriteRain896(OOKPPMDecoder):
    """Acurite 896 Rain Gauge.

    r_device: OOK_PULSE_PPM, short=1000, long=2000, reset=5000.
    Message: 24 bits (3 bytes).  ID | rain_counter (12 bits) = 0.5 mm / tip.
    """
    name     = "Acurite-Rain896"
    short_us = 1000.0
    long_us  = 2000.0
    reset_us = 5000.0
    n_bits   = 24

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 24, 8))
        sensor_id = b[0]
        rain_raw  = ((b[1] & 0x0F) << 8) | b[2]
        rain_mm   = rain_raw * 0.5
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":      sensor_id,
            "rain_mm": round(rain_mm, 1),
        })


__all__ = ["AcuriteRain896"]
