"""FineOffset WS2032 Weather Station."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8, checksum_sum
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class WS2032(OOKPWMDecoder):
    """FineOffset WS2032 Weather Station."""
    name       = "WS2032"
    short_us   = 500.0
    long_us    = 1_000.0
    reset_us   = 4_000.0
    n_bits     = 120       # generous window for preamble search
    max_offset = 10

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 112:
            return None

        # Data is transmitted inverted
        inv = [1 - x for x in bits]

        # Search for preamble byte 0x0A in the first several positions
        start = -1
        for off in range(min(len(inv) - 111, 16)):
            if bits_to_int(inv[off:off + 8]) == 0x0A:
                start = off
                break
        if start < 0 or start + 112 > len(inv):
            return None

        b = bytes(bits_to_int(inv[start + i:start + i + 8]) for i in range(0, 112, 8))

        # Additive sum checksum over bytes 0–11
        if checksum_sum(b[:12]) != b[12]:
            return None

        # CRC-8 poly=0x31 residue check over all 14 bytes (result must be 0)
        if crc8(b, poly=0x31, init=0x00) != 0:
            return None

        device_id      = (b[1] << 8) | b[2]
        battery_low    = b[3] & 0x01
        dir_raw        = b[4] >> 4
        temp_sign      = (b[4] >> 3) & 1          # 1 = negative
        temp_mag       = ((b[4] & 0x07) << 8) | b[5]
        temp_c         = (-temp_mag if temp_sign else temp_mag) * 0.1
        humidity       = b[6]
        wind_avg_km_h  = round(b[7] * 0.43 * 3.6, 1)
        wind_gust_km_h = round(b[8] * 0.43 * 3.6, 1)
        rain_raw       = (b[9] << 16) | (b[10] << 8) | b[11]

        if not 0 <= humidity <= 100:
            return None
        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
            "wind_avg_km_h": wind_avg_km_h,
            "wind_max_km_h": wind_gust_km_h,
            "wind_dir_deg":  round(dir_raw * 22.5, 1),
            "rain_mm":       rain_raw,
        })


__all__ = ["WS2032"]
