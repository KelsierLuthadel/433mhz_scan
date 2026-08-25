"""Shenzhen Wale WL-TH6R Temperature and Humidity Sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ._helpers import _sign16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ShenzhenWaleWLTH6R(OOKPWMDecoder):
    """Shenzhen Wale WL-TH6R Temperature and Humidity Sensor."""
    name      = "WL-TH6R"
    short_us  = 365.0
    long_us   = 605.0
    reset_us  = 4_000.0
    n_bits    = 72
    tolerance = 0.15   # ≈50 µs absolute tolerance (tight spec)

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 72:
            return None
        # Invert all bits
        b = bytearray(bits_to_int(bits[i:i + 8]) ^ 0xFF for i in range(0, 72, 8))

        # De-whiten: XOR bytes 0–6 with the control byte (b[7])
        key = b[7]
        for i in range(7):
            b[i] ^= key

        # Validate MIC
        xsum = 0
        bsum = 0
        for i in range(7):
            xsum ^= b[i]
            bsum += b[i]
        mic = 0xA5 ^ xsum ^ (bsum & 0xFF) ^ ((bsum >> 8) & 0xFF)
        if mic != b[8]:
            return None

        sensor_id   = (b[0] << 16) | (b[1] << 8) | b[2]
        temp_c      = _sign16((b[3] << 8) | b[4]) * 0.1
        humidity    = b[5]
        battery_pct = b[6]

        if not -20.0 <= temp_c <= 60.0:
            return None
        if humidity > 127:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:06X}",
            "battery_ok":    int(battery_pct >= 20),
            "battery_pct":   battery_pct,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["ShenzhenWaleWLTH6R"]
