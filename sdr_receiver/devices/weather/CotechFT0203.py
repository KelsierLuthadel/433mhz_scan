"""Cotech FT0203 / 18-3676 anemometer (72-bit Manchester)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class CotechFT0203(ManchesterDecoder):
    """Cotech FT0203 / 18-3676 anemometer (72-bit Manchester)."""
    name     = "Cotech-FT0203"
    chip_us  = 500.0
    reset_us = 1200.0
    n_bits   = 72

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 72:
            return None
        b = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 72, 8))
        # Sync byte must be 0x14
        if b[0] != 0x14:
            return None
        # CRC-8 (poly=0x31, init=0xC0) over first 8 bytes
        if crc8(b[:8], 0x31, 0xC0) != b[8]:
            return None
        # 11-bit ID: b[1] upper 8 bits + b[2] upper 3 bits
        device_id  = (b[1] << 3) | (b[2] >> 5)
        battery_ok = bool((b[2] >> 4) & 1)
        dir_msb    = (b[2] >> 1) & 1
        gust_msb   = (b[2] >> 2) & 1
        avg_msb    = (b[2] >> 3) & 1
        avg_ms     = ((avg_msb << 8) | b[3]) * 0.1
        gust_ms    = ((gust_msb << 8) | b[4]) * 0.1
        wind_dir   = (dir_msb << 8) | b[5]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id, "battery_ok": battery_ok,
            "wind_speed_ms":    round(avg_ms, 1),
            "wind_gust_ms":     round(gust_ms, 1),
            "wind_direction_deg": wind_dir,
        })


__all__ = ["CotechFT0203"]
