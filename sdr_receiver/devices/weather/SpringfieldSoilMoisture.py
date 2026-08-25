"""Springfield Temperature and Soil Moisture Station."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _xor_bytes(data: bytes | bytearray) -> int:
    result = 0
    for b in data:
        result ^= b
    return result


def _sign12(raw: int) -> int:
    """Sign-extend a 12-bit unsigned value to a signed int."""
    return raw - 0x1000 if raw >= 0x800 else raw


class SpringfieldSoilMoisture(OOKPPMDecoder):
    """Springfield Temperature and Soil Moisture Station."""
    name     = "Springfield-TH"
    short_us = 2_000.0
    long_us  = 4_000.0
    reset_us = 9_200.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 32, 8))

        # XOR fold: XOR bytes 0–3, then nibble-fold; result must be 0
        full_xor = _xor_bytes(b)
        if (full_xor >> 4) ^ (full_xor & 0x0F):
            return None

        sensor_id   = b[0]
        battery_low = (b[1] >> 7) & 1
        channel     = ((b[1] >> 4) & 0x3) + 1   # 0-indexed → 1–3
        temp_c      = _sign12(((b[1] & 0x0F) << 8) | b[2]) * 0.1
        moisture    = ((b[3] >> 4) & 0x0F) * 10  # nibble × 10 = %

        if not -30.0 <= temp_c <= 70.0:
            return None
        if not 0 <= moisture <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "moisture":      moisture,
        })


__all__ = ["SpringfieldSoilMoisture"]
