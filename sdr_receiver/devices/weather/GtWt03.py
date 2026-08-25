"""Globaltronics GT-WT-03 temperature and humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _chk_rollbyte(buf: bytes, n: int, gen: int) -> int:
    """Galois/Fibonacci LFSR-16 rolling checksum used by GT-WT-03."""
    chk = 0
    key = gen & 0xFFFF
    for i in range(n):
        for j in range(7, -1, -1):
            if (buf[i] >> j) & 1:
                chk ^= key & 0xFF
            if key & 0x01:
                key = ((key >> 1) ^ gen) & 0xFFFF
            else:
                key = (key >> 1) & 0xFFFF
    return chk & 0xFF


class GtWt03(OOKPWMDecoder):
    """Globaltronics GT-WT-03 temperature and humidity sensor."""
    name     = "GT-WT-03"
    short_us = 256.0
    long_us  = 625.0
    reset_us = 61000.0
    n_bits   = 41

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 40:
            return None
        b = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 40, 8))
        # LFSR-16 checksum: chk_rollbyte(b, 4, 0x3100) ^ b[4] ^ 0x2D == 0
        if (_chk_rollbyte(b, 4, 0x3100) ^ b[4] ^ 0x2D) != 0:
            return None
        device_id  = b[0]
        humidity   = b[1]
        battery_ok = not bool((b[2] >> 7) & 1)
        button     = bool((b[2] >> 6) & 1)
        channel    = ((b[2] >> 4) & 0x03) + 1
        # 12-bit 2's complement temperature (sign-extended via 16-bit shift)
        temp16 = ((b[2] & 0x0F) << 12) | (b[3] << 4)
        if temp16 >= 32768:
            temp16 -= 65536
        temp_c = (temp16 >> 4) / 10.0
        # Sentinel humidity values
        if humidity == 10:
            humidity = 0
        elif humidity == 110:
            humidity = 100
        elif not 20 <= humidity <= 95:
            return None
        if not -50.0 <= temp_c <= 70.0:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id, "channel": channel, "battery_ok": battery_ok,
            "button": button,
            "temperature_C": round(temp_c, 1), "humidity": humidity,
        })


__all__ = ["GtWt03"]
