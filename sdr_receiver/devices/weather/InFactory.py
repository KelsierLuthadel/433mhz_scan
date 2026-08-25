"""InFactory NC-3982-913 / nor-tec / FreeTec temperature/humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _crc4(data: bytes, poly: int = 0x13, init: int = 0x00) -> int:
    """CRC-4 per rtl_433's crc4(): operates on full bytes, result in high nibble."""
    poly_shifted = (poly << 4) & 0xFF
    rem = (init & 0xF) << 4
    for byte in data:
        rem = (rem ^ byte) & 0xFF
        for _ in range(8):
            if rem & 0x80:
                rem = ((rem << 1) ^ poly_shifted) & 0xFF
            else:
                rem = (rem << 1) & 0xFF
    return rem >> 4


class InFactory(OOKPPMDecoder):
    """InFactory NC-3982-913 / nor-tec / FreeTec temperature/humidity sensor."""
    name     = "InFactory-TH"
    short_us = 2_000.0
    long_us  = 4_000.0
    reset_us = 5_000.0
    n_bits   = 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 40:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8)]

        channel = b[4] & 0x03
        if not channel:
            return None

        # CRC-4 over b[0:4]; stored in b[4] >> 4
        if _crc4(bytes(b[:4]), poly=0x13, init=0x00) != (b[4] >> 4):
            return None

        device_id   = b[0]
        tx_button   = (b[1] >> 3) & 1
        battery_low = (b[1] >> 2) & 1

        temp_raw = (b[2] << 4) | (b[3] >> 4)
        temp_f   = (temp_raw - 900) * 0.1
        temp_c   = (temp_f - 32.0) * 5.0 / 9.0

        humidity = (b[3] & 0x0F) * 10 + (b[4] >> 4)

        if not -50.0 <= temp_c <= 80.0:
            return None
        if not 0 <= humidity <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "button":        tx_button,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["InFactory"]
