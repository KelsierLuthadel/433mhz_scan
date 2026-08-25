"""Cotech 36-7959 / SwitchDocLabs FT020T wireless weather station."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Cotech36_7959(ManchesterDecoder):
    """Cotech 36-7959 / SwitchDocLabs FT020T wireless weather station."""
    name     = "Cotech-36-7959"
    chip_us  = 500.0
    reset_us = 1200.0
    n_bits   = 112

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 112:
            return None
        b = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 112, 8))
        # CRC-8 (poly=0x31, init=0xC0) over first 13 bytes, result in b[13]
        if crc8(b[:13], 0x31, 0xC0) != b[13]:
            return None
        device_id  = b[0]
        battery_ok = bool((b[1] >> 3) & 1)
        # Wind speed: MSB flag in b[1] bit0, 8-bit value in b[2]
        wind_spd_ms   = (((b[1] & 0x01) << 8) | b[2]) * 0.1
        # Wind gust: MSB flag in b[1] bit1, 8-bit value in b[3]
        wind_gust_ms  = (((b[1] & 0x02) << 7) | b[3]) * 0.1
        # Wind direction: MSB flag in b[1] bit2, 8-bit value in b[4]
        wind_dir_deg  = ((b[1] & 0x04) << 6) | b[4]
        # Rain: 12-bit value
        rain_mm       = (((b[5] & 0x0F) << 8) | b[6]) * 0.3
        # Temperature: 12-bit, (raw - 400) * 0.1 °C
        temp_raw      = ((b[7] & 0x0F) << 8) | b[8]
        temp_c        = (temp_raw - 400) / 10.0
        humidity      = b[9]
        uv_index      = b[10]
        fields: dict = {
            "id": device_id, "battery_ok": battery_ok,
            "wind_speed_ms":    round(wind_spd_ms, 1),
            "wind_gust_ms":     round(wind_gust_ms, 1),
            "wind_direction_deg": wind_dir_deg,
            "rain_mm":          round(rain_mm, 1),
            "temperature_C":    round(temp_c, 1),
            "humidity":         humidity,
        }
        if uv_index <= 150:
            fields["uv_index"] = uv_index
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["Cotech36_7959"]
