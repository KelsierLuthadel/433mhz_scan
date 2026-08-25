"""Acurite Temperature + Humidity sensor (generic TH series)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AcuriteTH(OOKPPMDecoder):
    """Acurite Temperature + Humidity sensor (generic TH series).

    r_device: OOK_PULSE_PPM, short=1000, long=2000, reset=10000.
    Message: 40 bits (5 bytes).
      b[0]       = ID
      b[1] bits  = battery(6), ?(5-4), channel(3-2), temp_high(1-0)
      b[2]       = temp_low (12-bit signed total, ×0.1 °C)
      b[3]       = humidity (%)
      b[4]       = checksum (sum b[0:4] & 0xFF)
    """
    name     = "Acurite-TH"
    short_us = 1000.0
    long_us  = 2000.0
    reset_us = 10_000.0
    n_bits   = 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8))
        if (sum(b[:4]) & 0xFF) != b[4]:
            return None
        sensor_id  = b[0]
        battery_ok = bool(b[1] & 0x40)   # bit 6 high = good
        temp_raw   = ((b[1] & 0x0F) << 8) | b[2]
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c   = temp_raw / 10.0
        humidity = b[3]
        if not -50.0 <= temp_c <= 70.0:
            return None
        if not 0 <= humidity <= 100:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["AcuriteTH"]
