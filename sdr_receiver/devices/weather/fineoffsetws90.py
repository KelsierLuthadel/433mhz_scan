"""Fine Offset WS90 all-in-one weather station (adds barometric pressure)."""
from __future__ import annotations
from ...dsp import crc8, checksum_sum
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWS90(_FineOffsetFSKBase):
    """Fine Offset WS90 all-in-one weather station (adds barometric pressure).

    Protocol: FSK_PULSE_PCM, chip ≈ 58 µs, 32 payload bytes.
    Sensor type byte: 0x90.
    Byte layout:
      [type:8=0x90][id:24]
      bytes4-5:  light (× 10 lux)
      byte6:     battery voltage (× 20 mV)
      byte7:     flags [temp_msb(2b), wind_msb(1b), bear_msb(1b), gust_msb(1b), ...]
      byte8:     temperature low 8 bits  → 10-bit raw / 10.0 − 40.0 °C
      byte9:     humidity
      byte10:    wind speed low 8 bits   → 9-bit raw / 10.0 m/s
      byte11:    wind bearing low 8 bits → 9-bit, degrees
      byte12:    wind gust low 8 bits    → 9-bit raw / 10.0 m/s
      byte13:    UV index × 10
      bytes14-15: pressure (big-endian, × 0.1 hPa)
      bytes16-20: rain data
      byte21:    supercap voltage (bits 5:0, × 0.1 V)
      bytes22-28: reserved
      byte29:    firmware version
      byte30:    additive checksum (sum bytes 0–29)
      byte31:    CRC-8 (poly 0x31, bytes 0–30)
    """
    name     = "Fine Offset WS90"
    bit_rate = 1_000_000 / 58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 32)
        if data is None or data[0] != 0x90:
            return None
        if checksum_sum(data[:30]) != data[30]:
            return None
        if crc8(data[:31], 0x31, 0x00) != data[31]:
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
        pressure  = ((data[14] << 8) | data[15]) / 10.0
        supercap_v = (data[21] & 0x3F) * 0.1
        firmware  = data[29]

        if not -40.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "battery_ok":    battery_ok,
            "battery_mV":    bat_mv,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
            "pressure_hPa":  round(pressure, 1),
            "wind_dir_deg":  bearing,
            "wind_avg_m_s":  round(wind_ms, 2),
            "wind_max_m_s":  round(gust_ms, 2),
            "uv_index":      round(uv_index, 1),
            "light_lux":     light_lux,
            "supercap_V":    round(supercap_v, 1),
            "firmware":      firmware,
            "mic":           "CRC",
        })


__all__ = ["FineOffsetWS90"]
