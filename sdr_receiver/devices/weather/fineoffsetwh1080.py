"""Fine Offset WH1080 / WH3080 OOK weather station."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


# 16-point compass bearing lookup (index = direction byte raw value)
_WH1080_WIND_DIR = [
    315.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 0.0,
    247.5, 292.5, 337.5, 22.5, 202.5, 157.5, 112.5, 67.5,
]


class FineOffsetWH1080(OOKPWMDecoder):
    """Fine Offset WH1080 / WH3080 OOK weather station.

    Protocol: OOK_PULSE_PWM, 88 bits (11 bytes).
    Byte layout (nibble notation, each letter = 4 bits):
      [ff][F][I I][T T T][H H][S S][G G][? R R][B][D D][C C]
    F = format nibble (0xA=weather, 0xB=datetime, 0x7=UV/Light)
    CRC-8: polynomial 0x31, init 0xFF, over all 11 bytes.
    Temperature: (raw − 400) / 10.0 °C.
    Wind/Gust:   raw × 0.34 m/s.  Rain: raw × 0.3 mm.
    """
    name      = "Fine Offset WH1080"
    short_us  = 544.0
    long_us   = 1_524.0
    reset_us  = 2_800.0
    n_bits    = 88

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 88:
            return None

        data = bytes(bits_to_int(bits[i : i + 8]) for i in range(0, 88, 8))
        crc_recv = data[10]
        if crc8(data[:10], 0x31, 0xFF) != crc_recv:
            return None

        fmt       = (data[1] >> 4) & 0x0F
        device_id = ((data[1] & 0x0F) << 4) | (data[2] >> 4)

        if fmt == 0xA:  # weather packet
            temp_raw  = ((data[2] & 0x0F) << 8) | data[3]
            temp_c    = (temp_raw - 400) / 10.0
            humidity  = data[4]
            wind_raw  = data[5]
            gust_raw  = data[6]
            rain_raw  = ((data[7] & 0x0F) << 8) | data[8]
            bat_flags = (data[9] >> 4) & 0x0F
            dir_raw   = data[9] & 0x0F
            battery_ok = bool((bat_flags >> 3) & 1)
            wind_dir  = _WH1080_WIND_DIR[dir_raw] if dir_raw < 16 else 0.0

            if not -60.0 <= temp_c <= 80.0:
                return None
            if not 0 <= humidity <= 100:
                return None

            return DecodedPacket.from_fields(self.name, freq_hz, {
                "id":            device_id,
                "battery_ok":    battery_ok,
                "temperature_C": round(temp_c, 1),
                "humidity":      humidity,
                "wind_dir_deg":  wind_dir,
                "wind_avg_m_s":  round(wind_raw * 0.34, 2),
                "wind_max_m_s":  round(gust_raw * 0.34, 2),
                "rain_mm":       round(rain_raw * 0.3, 1),
                "mic":           "CRC",
            })

        if fmt == 0xB:  # datetime packet
            hour   = data[2] & 0x1F
            minute = data[3] & 0x3F
            second = data[4] & 0x3F
            return DecodedPacket.from_fields(self.name, freq_hz, {
                "id":         device_id,
                "msg_type":   "datetime",
                "radio_clock": f"{hour:02d}:{minute:02d}:{second:02d}",
                "mic":        "CRC",
            })

        return None


__all__ = ["FineOffsetWH1080"]
