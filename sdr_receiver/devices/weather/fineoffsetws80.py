"""Fine Offset WS80 all-in-one ultrasonic weather station."""
from __future__ import annotations
from ...dsp import crc8, checksum_sum
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWS80(_FineOffsetFSKBase):
    """Fine Offset WS80 all-in-one ultrasonic weather station.

    Protocol: FSK_PULSE_PCM, chip ≈ 58 µs, 18 payload bytes.
    Sensor type byte: 0x80.
    Byte layout:
      [type:8=0x80][id:24]
      bytes4-5: light (× 10 lux)
      byte6:    battery voltage (× 20 mV)
      byte7:    flags [temp_msb(2b), wind_msb(1b), bear_msb(1b), gust_msb(1b), ...]
      byte8:    temperature low 8 bits  → 10-bit: temp_raw/10.0 − 40.0 °C
      byte9:    humidity
      byte10:   wind speed low 8 bits   → 9-bit raw / 10.0 m/s
      byte11:   wind bearing low 8 bits → 9-bit, degrees
      byte12:   wind gust low 8 bits    → 9-bit raw / 10.0 m/s
      byte13:   UV index × 10
      bytes14-15: reserved
      byte16:   CRC-8 (poly 0x31, bytes 0–15)
      byte17:   additive checksum (sum bytes 0–16)
    """
    name     = "Fine Offset WS80"
    bit_rate = 1_000_000 / 58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 18)
        if data is None or data[0] != 0x80:
            return None
        if crc8(data[:16], 0x31, 0x00) != data[16]:
            return None
        if checksum_sum(data[:17]) != data[17]:
            return None

        device_id = (data[1] << 16) | (data[2] << 8) | data[3]
        light_lux = ((data[4] << 8) | data[5]) * 10
        bat_mv    = data[6] * 20
        battery_ok = bat_mv >= 2300
        flags     = data[7]

        temp_msb  = (flags >> 6) & 0x03
        wind_msb  = (flags >> 5) & 0x01
        bear_msb  = (flags >> 4) & 0x01
        gust_msb  = (flags >> 3) & 0x01

        temp_raw  = (temp_msb << 8) | data[8]
        temp_c    = temp_raw / 10.0 - 40.0
        humidity  = data[9]
        wind_raw  = (wind_msb << 8) | data[10]
        wind_ms   = wind_raw / 10.0
        bearing   = (bear_msb << 8) | data[11]
        gust_raw  = (gust_msb << 8) | data[12]
        gust_ms   = gust_raw / 10.0
        uv_index  = data[13] / 10.0

        if not -40.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "battery_ok":    battery_ok,
            "battery_mV":    bat_mv,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
            "wind_dir_deg":  bearing,
            "wind_avg_m_s":  round(wind_ms, 2),
            "wind_max_m_s":  round(gust_ms, 2),
            "uv_index":      round(uv_index, 1),
            "light_lux":     light_lux,
            "mic":           "CRC",
        })


__all__ = ["FineOffsetWS80"]
