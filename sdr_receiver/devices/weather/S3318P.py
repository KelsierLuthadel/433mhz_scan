"""Conrad S3318P / Renkforce temperature and humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _crc4(data: bytes, poly: int = 0x3, init: int = 0x0) -> int:
    """CRC-4 (nibble-wise, MSB-first) used by Kedsum / S3318P."""
    remainder = (init & 0xF) << 4
    for byte in data:
        remainder ^= byte
        for _ in range(8):
            if remainder & 0x80:
                remainder = ((remainder << 1) ^ (poly << 4)) & 0xFF
            else:
                remainder = (remainder << 1) & 0xFF
    return remainder >> 4


class S3318P(OOKPPMDecoder):
    """Conrad S3318P / Renkforce temperature and humidity sensor."""
    name     = "S3318P"
    short_us = 1900.0
    long_us  = 3800.0
    reset_us = 9400.0
    n_bits   = 42

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[2 + i:2 + i + 8]) for i in range(0, 40, 8))
        # CRC-4 over b[0:4]
        crc_calc = _crc4(b[:4])
        if crc_calc ^ (b[4] >> 4) != (b[4] & 0x0F):
            return None
        device_id  = b[0]
        channel    = ((b[1] >> 4) & 0x03) + 1
        button     = bool(b[4] >> 7)
        battery_ok = not bool((b[4] >> 6) & 1)
        temp_raw   = ((b[1] & 0x0F) << 8) | b[2]
        temp_f     = (temp_raw - 900) / 10.0
        temp_c     = (temp_f - 32.0) / 1.8
        humidity   = ((b[3] & 0x0F) << 4) | (b[3] >> 4)
        if not 0 <= humidity <= 100:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id, "channel": channel, "battery_ok": battery_ok,
            "button": button,
            "temperature_F": round(temp_f, 1),
            "temperature_C": round(temp_c, 1),
            "humidity": humidity,
        })


__all__ = ["S3318P"]
