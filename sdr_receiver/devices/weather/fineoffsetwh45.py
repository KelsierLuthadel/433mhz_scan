"""Fine Offset WH45 air quality + CO2 sensor."""
from __future__ import annotations
from ...dsp import crc8, checksum_sum
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWH45(_FineOffsetFSKBase):
    """Fine Offset WH45 air quality + CO₂ sensor.

    Protocol: FSK_PULSE_PCM, chip ≈ 58 µs, 15 payload bytes.
    Byte layout after sync:
      [type:8=0x45][id:24]
      byte4: [bat:4][temp_hi:4]  byte5: temp_lo:8
        → temp_raw = ((byte4 & 0x07) << 8) | byte5; bat = (byte4>>4)&0x07
      byte6: humidity
      byte7: [pm25_hi:6...] byte8: pm25_lo → 14-bit PM2.5 × 0.1 µg/m³
      byte9: [pm10_hi:6...] byte10: pm10_lo → 14-bit PM10 × 0.1 µg/m³
      bytes11-12: CO₂ ppm (16-bit big-endian)
      byte13: CRC-8 (poly 0x31, bytes 0–12)
      byte14: additive checksum (sum bytes 0–13)
    Temperature: temp_raw / 10.0 − 40.0 °C.
    Battery bars: 0–5; value 6 = USB/external power.
    """
    name     = "Fine Offset WH45"
    bit_rate = 1_000_000 / 58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 15)
        if data is None or data[0] != 0x45:
            return None
        if crc8(data[:13], 0x31, 0x00) != data[13]:
            return None
        if checksum_sum(data[:14]) != data[14]:
            return None

        device_id = (data[1] << 16) | (data[2] << 8) | data[3]
        bat_raw   = (data[4] >> 4) & 0x07
        temp_raw  = ((data[4] & 0x07) << 8) | data[5]
        temp_c    = temp_raw / 10.0 - 40.0
        humidity  = data[6]
        pm25_raw  = ((data[7] & 0x3F) << 8) | data[8]
        pm10_raw  = ((data[9] & 0x3F) << 8) | data[10]
        co2_ppm   = (data[11] << 8) | data[12]
        ext_power = bat_raw == 6
        battery_ok = ext_power or bat_raw >= 1

        if not -40.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           device_id,
            "battery_ok":   battery_ok,
            "ext_power":    ext_power,
            "temperature_C": round(temp_c, 1),
            "humidity":     humidity,
            "pm2_5_ug_m3":  round(pm25_raw * 0.1, 1),
            "pm10_ug_m3":   round(pm10_raw * 0.1, 1),
            "co2_ppm":      co2_ppm,
            "mic":          "CRC",
        })


__all__ = ["FineOffsetWH45"]
