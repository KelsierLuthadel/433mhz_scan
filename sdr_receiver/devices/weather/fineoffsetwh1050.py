"""Fine Offset WH1050 / TFA 30.3151 OOK weather station."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class FineOffsetWH1050(OOKPWMDecoder):
    """Fine Offset WH1050 / TFA 30.3151 OOK weather station.

    Protocol: OOK_PULSE_PWM, 72 bits (9 bytes).
    Byte layout (MSB first):
      [msg_type:4][id:8][?:1][bat:1][temp:10][hum:8][wind:8][gust:8][rain:16][crc8:8]
    CRC-8: polynomial 0x31, init 0x00, over bytes 0–7.
    Temperature: raw / 10.0 − 40.0 °C.
    Wind: raw × 0.34 m/s.  Rain: raw × 0.3 mm.
    """
    name      = "Fine Offset WH1050"
    short_us  = 544.0
    long_us   = 1_524.0
    reset_us  = 10_520.0
    n_bits    = 72

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 72:
            return None
        msg_type = bits_to_int(bits[0:4])
        if msg_type not in (5, 6):
            return None

        device_id  = bits_to_int(bits[4:12])
        battery_ok = bool(bits[13])
        temp_raw   = bits_to_int(bits[14:24])
        temp_c     = temp_raw / 10.0 - 40.0
        humidity   = bits_to_int(bits[24:32])

        data = bytes(bits_to_int(bits[i : i + 8]) for i in range(0, 64, 8))
        crc_recv = bits_to_int(bits[64:72])
        if crc8(data, 0x31, 0x00) != crc_recv:
            return None
        if not -50.0 <= temp_c <= 80.0:
            return None
        if not 0 <= humidity <= 100:
            return None

        if msg_type == 6:
            # Time packet  minimal decode
            return DecodedPacket.from_fields(self.name, freq_hz, {
                "id": device_id, "msg_type": msg_type, "battery_ok": battery_ok,
            })

        wind_raw  = bits_to_int(bits[32:40])
        gust_raw  = bits_to_int(bits[40:48])
        rain_raw  = bits_to_int(bits[48:64])
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":             device_id,
            "msg_type":       msg_type,
            "battery_ok":     battery_ok,
            "temperature_C":  round(temp_c, 1),
            "humidity":       humidity,
            "wind_avg_m_s":   round(wind_raw * 0.34, 2),
            "wind_max_m_s":   round(gust_raw * 0.34, 2),
            "rain_mm":        round(rain_raw * 0.3, 1),
            "mic":            "CRC",
        })


__all__ = ["FineOffsetWH1050"]
