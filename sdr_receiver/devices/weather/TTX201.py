"""Emos TTX201 Manchester-encoded temperature sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TTX201(ManchesterDecoder):
    """Emos TTX201 Manchester-encoded temperature sensor."""
    name      = "Emos-TTX201"
    chip_us   = 510.0
    reset_us  = 1700.0
    tolerance = 250.0 / 510.0   # ≈ 0.49
    n_bits    = 54

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 48:
            return None
        b = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 48, 8))
        # Upper 2 bits of b[0] must be 0 (start marker)
        if (b[0] >> 6) != 0:
            return None
        # Validate 6-bit checksum = sum of nibbles of b[1..5] mod 64
        chk      = b[0] & 0x3F
        nibble_sum = sum((b[i] >> 4) + (b[i] & 0x0F) for i in range(1, 6))
        if chk != (nibble_sum & 0x3F):
            return None
        # Postmark must be 0x14 for TTX201
        postmark = b[5]
        if postmark != 0x14:
            return None
        sensor_id  = b[1]
        battery_ok = not bool((b[2] >> 3) & 1)
        channel    = (b[2] & 0x07) + 1
        # 12-bit signed temperature: lower nibble of b[3] (high) + b[4] (low)
        temp16 = ((b[3] & 0x0F) << 12) | (b[4] << 4)
        if temp16 >= 32768:
            temp16 -= 65536
        temp_c = (temp16 >> 4) / 10.0
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": sensor_id, "channel": channel, "battery_ok": battery_ok,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["TTX201"]
