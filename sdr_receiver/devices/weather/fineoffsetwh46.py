"""Fine Offset WH46 extended air quality sensor (PM1/PM2.5/PM4/PM10 + CO2)."""
from __future__ import annotations
from ...dsp import crc8, checksum_sum
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWH46(_FineOffsetFSKBase):
    """Fine Offset WH46 extended air quality sensor (PM1/PM2.5/PM4/PM10 + CO₂).

    Protocol: FSK_PULSE_PCM, chip ≈ 58 µs, 21 payload bytes.
    Byte layout after sync:
      [type:8=0x46][id:24]
      bytes4-5: temperature (11-bit, (raw−400)×0.1 °C)
      byte6: humidity
      bytes7-10: battery + PM2.5 + PM10
      bytes11-12: CO₂ ppm
      bytes13-16: PM1 + PM4
      bytes17-18: constant 0x0190
      byte19: CRC-8 (poly 0x31, bytes 0–18)
      byte20: additive checksum (sum bytes 0–19)
    """
    name     = "Fine Offset WH46"
    bit_rate = 1_000_000 / 58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 21)
        if data is None or data[0] != 0x46:
            return None
        if crc8(data[:19], 0x31, 0x00) != data[19]:
            return None
        if checksum_sum(data[:20]) != data[20]:
            return None

        device_id = (data[1] << 16) | (data[2] << 8) | data[3]
        temp_raw  = ((data[4] & 0x07) << 8) | data[5]
        temp_c    = (temp_raw - 400) / 10.0
        humidity  = data[6]
        bat_raw   = (data[7] >> 5) & 0x07
        pm25_raw  = ((data[7] & 0x1F) << 8) | data[8]
        pm10_raw  = ((data[9] & 0x3F) << 8) | data[10]
        co2_ppm   = (data[11] << 8) | data[12]
        pm1_raw   = ((data[13] & 0x3F) << 8) | data[14]
        pm4_raw   = ((data[15] & 0x3F) << 8) | data[16]
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
            "pm1_ug_m3":    round(pm1_raw * 0.1, 1),
            "pm2_5_ug_m3":  round(pm25_raw * 0.1, 1),
            "pm4_ug_m3":    round(pm4_raw * 0.1, 1),
            "pm10_ug_m3":   round(pm10_raw * 0.1, 1),
            "co2_ppm":      co2_ppm,
            "mic":          "CRC",
        })


__all__ = ["FineOffsetWH46"]
