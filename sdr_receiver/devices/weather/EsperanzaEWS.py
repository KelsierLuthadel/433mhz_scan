"""Esperanza EWS-103 Temperature and Humidity Sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _crc4(data: bytes, poly: int = 0x3, init: int = 0x0) -> int:
    """4-bit CRC, MSB-first (rtl_433 crc4 convention)."""
    crc = init & 0xF
    for byte in data:
        for i in range(7, -1, -1):
            bit = (byte >> i) & 1
            if ((crc >> 3) & 1) ^ bit:
                crc = ((crc << 1) & 0xF) ^ poly
            else:
                crc = (crc << 1) & 0xF
    return crc


class EsperanzaEWS(OOKPPMDecoder):
    """Esperanza EWS-103 Temperature and Humidity Sensor."""
    name     = "Esperanza-EWS"
    short_us = 2_000.0
    long_us  = 4_000.0
    reset_us = 9_400.0
    n_bits   = 42

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 42:
            return None
        # 40-bit payload starts at bit 2
        payload = bits[2:42]
        b = bytes(bits_to_int(payload[i:i + 8]) for i in range(0, 40, 8))

        # CRC-4 over bytes 0–3 vs lower nibble of b[4]
        if _crc4(b[:4], poly=0x3, init=0x0) != (b[4] & 0x0F):
            return None

        device_id  = b[0]
        channel    = ((b[1] >> 4) & 0x3) + 1   # 0-indexed → 1–3
        battery_ok = (b[4] >> 6) & 1

        # Temperature: (raw − 900) × 0.1 °F, then convert to °C
        temp_raw = ((b[1] & 0x0F) << 8) | b[2]
        temp_f   = (temp_raw - 900) * 0.1
        temp_c   = round((temp_f - 32.0) / 1.8, 1)

        # Humidity: nibble-swap b[3]
        humidity = ((b[3] & 0x0F) << 4) | (b[3] >> 4)

        if not 0 <= humidity <= 100:
            return None
        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "temperature_C": temp_c,
            "humidity":      humidity,
        })


__all__ = ["EsperanzaEWS"]
