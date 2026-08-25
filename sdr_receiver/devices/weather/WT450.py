"""WT450 / WT260H / WT405H temperature/humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class WT450(ManchesterDecoder):
    """WT450 / WT260H / WT405H temperature/humidity sensor."""
    name     = "WT450-TH"
    chip_us  = 976.0
    reset_us = 18_000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 32, 8)]  # b[0..3]
        b4 = bits_to_int(bits[32:36]) << 4  # upper nibble of b[4]

        # Preamble check
        if (b[0] >> 4) != 0xC:
            return None

        # XOR parity over 5 bytes (b[4] upper nibble is enough for parity)
        parity = b[0] ^ b[1] ^ b[2] ^ b[3] ^ b4
        parity ^= (parity >> 4)
        parity ^= (parity >> 2)
        parity &= 0x3
        if parity:
            return None

        house_code  = b[0] & 0x0F
        channel     = (b[1] >> 6) + 1
        battery_low = bool(b[1] & 0x08)
        humidity    = ((b[1] & 0x07) << 4) | (b[2] >> 4)
        temp_whole  = ((b[2] & 0x0F) << 4) | (b[3] >> 4)
        temp_frac   = b[3] & 0x0F
        temp_c      = (temp_whole - 50.0) + (temp_frac / 16.0)
        seq         = (b4 >> 6) & 0x03

        if not 0 <= humidity <= 100:
            return None
        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            house_code,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 2),
            "humidity":      humidity,
            "seq":           seq,
        })


__all__ = ["WT450"]
