"""Geevon TX19-1 outdoor temperature/humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _lfsr_digest8_reflect(data: bytes, gen: int, key: int) -> int:
    """Galois LFSR digest-8, LSB-first (reflected) bit order.
    Matches rtl_433's lfsr_digest8_reverse() / lfsr_digest8_reflect()."""
    result = 0
    k = key & 0xFF
    for byte in data:
        for i in range(8):
            if (byte >> i) & 1:
                result ^= k
            if k & 0x01:
                k = (k >> 1) ^ gen
            else:
                k >>= 1
    return result & 0xFF


class GeevonTX19(OOKPWMDecoder):
    """Geevon TX19-1 outdoor temperature/humidity sensor."""
    name     = "Geevon-TX19"
    short_us = 250.0
    long_us  = 500.0
    reset_us = 1_700.0
    n_bits   = 73

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 73:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 72, 8))

        # Fixed sync byte validation
        if b[5] != 0xAA or b[6] != 0x55 or b[7] != 0xAA:
            return None

        # LFSR reflected checksum
        if _lfsr_digest8_reflect(b[:8], gen=0x98, key=0x25) != b[8]:
            return None

        battery_low = (b[1] >> 7) & 1
        channel     = ((b[1] & 0x30) >> 4) + 1
        temp_raw    = (b[2] << 4) | (b[3] >> 4)
        temp_c      = (temp_raw - 500) * 0.1
        humidity    = b[4]

        if not -50.0 <= temp_c <= 80.0:
            return None
        if not 0 <= humidity <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            b[0],
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["GeevonTX19"]
