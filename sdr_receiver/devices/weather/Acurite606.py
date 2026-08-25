"""Acurite 606TX Temperature Sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _lfsr_digest8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Acurite606(OOKPPMDecoder):
    """Acurite 606TX Temperature Sensor.

    r_device: OOK_PULSE_PPM, short=2000, long=4000, reset=10000.
    Message: 32 bits (4 bytes).
      b[0]       = ID
      b[1] bits  = battery(7), channel(5-4), temp_hi(3-0)
      b[2]       = temp_lo  → 12-bit signed ×0.1 °C
      b[3]       = LFSR-8 digest (poly=0x98, seed=0xF1) over b[0:3]
    """
    name     = "Acurite-606TX"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 10_000.0
    n_bits   = 32

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 32, 8))
        if _lfsr_digest8(b[:3], gen=0x98, key=0xF1) != b[3]:
            return None
        sensor_id  = b[0]
        battery_ok = not bool(b[1] & 0x80)
        channel    = ((b[1] & 0x30) >> 4) + 1
        temp_raw   = ((b[1] & 0x0F) << 8) | b[2]
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c = temp_raw / 10.0
        if not -50.0 <= temp_c <= 70.0:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["Acurite606"]
