"""Fine Offset WS85 solar-powered weather station (wind + rain + supercap)."""
from __future__ import annotations
from ...dsp import crc8, checksum_sum
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWS85(_FineOffsetFSKBase):
    """Fine Offset WS85 solar-powered weather station (wind + rain + supercap).

    Protocol: FSK_PULSE_PCM, chip ≈ 58 µs, 28 payload bytes.
    Sensor type byte: 0x85.
    Byte layout:
      [type:8=0x85][id:24]
      byte4:  battery voltage (× 20 mV)
      byte5:  flags [wind_msb, bearing_msb, gust_msb, ...]
      byte6:  reserved
      byte7:  wind speed low 8 bits   → 9-bit raw / 10.0 m/s
      byte8:  wind bearing low 8 bits → 9-bit, degrees
      byte9:  wind gust low 8 bits    → 9-bit raw / 10.0 m/s
      bytes10-11: reserved
      byte12: rain start detection bit (bit 0)
      bytes13-14: reserved
      bytes15-16: rain total (× 0.1 mm)
      byte17: supercap voltage (bits 5:0, × 0.1 V)
      bytes18-24: reserved
      byte25: firmware version
      byte26: CRC-8 (poly 0x31, bytes 0–25)
      byte27: additive checksum (sum bytes 0–26)
    """
    name     = "Fine Offset WS85"
    bit_rate = 1_000_000 / 58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 28)
        if data is None or data[0] != 0x85:
            return None
        if crc8(data[:26], 0x31, 0x00) != data[26]:
            return None
        if checksum_sum(data[:27]) != data[27]:
            return None

        device_id = (data[1] << 16) | (data[2] << 8) | data[3]
        bat_mv    = data[4] * 20
        battery_ok = bat_mv >= 2300
        flags     = data[5]

        wind_msb  = (flags >> 7) & 0x01
        bear_msb  = (flags >> 6) & 0x01
        gust_msb  = (flags >> 5) & 0x01

        wind_raw  = (wind_msb << 8) | data[7]
        wind_ms   = wind_raw / 10.0
        bearing   = (bear_msb << 8) | data[8]
        gust_raw  = (gust_msb << 8) | data[9]
        gust_ms   = gust_raw / 10.0
        rain_start = bool(data[12] & 0x01)
        rain_raw  = (data[15] << 8) | data[16]
        rain_mm   = rain_raw * 0.1
        supercap_v = (data[17] & 0x3F) * 0.1
        firmware  = data[25]

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           device_id,
            "battery_ok":   battery_ok,
            "battery_mV":   bat_mv,
            "wind_dir_deg": bearing,
            "wind_avg_m_s": round(wind_ms, 2),
            "wind_max_m_s": round(gust_ms, 2),
            "rain_mm":      round(rain_mm, 1),
            "rain_start":   rain_start,
            "supercap_V":   round(supercap_v, 1),
            "firmware":     firmware,
            "mic":          "CRC",
        })


__all__ = ["FineOffsetWS85"]
