"""Generic Temperature Sensor 1."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _sign16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class GenericTemperatureSensor(OOKPPMDecoder):
    """Generic Temperature Sensor 1."""
    name     = "Generic-Temperature"
    short_us = 2_000.0
    long_us  = 4_000.0
    reset_us = 10_000.0
    n_bits   = 24

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 24:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 24, 8))

        if (b[0] == 0 and b[1] == 0 and b[2] == 0) or \
           (b[0] == 0xFF and b[1] == 0xFF and b[2] == 0xFF):
            return None

        device_id = b[0]
        battery   = (b[1] & 0xC0) >> 6

        # 12-bit temp left-aligned: bits [15:4] carry temp × 10 as signed int
        temp_c = (_sign16(((b[1] & 0x3F) << 10) | (b[2] << 2)) >> 4) * 0.1

        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "battery_ok":    int(battery > 0),
            "temperature_C": round(temp_c, 2),
        })


__all__ = ["GenericTemperatureSensor"]
