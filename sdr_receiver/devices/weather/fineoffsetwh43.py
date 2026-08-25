"""Fine Offset WH43 air quality sensor (PM2.5 + PM10)."""
from __future__ import annotations
from ...dsp import crc8
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWH43(_FineOffsetFSKBase):
    """Fine Offset WH43 air quality sensor (PM2.5 + PM10).

    Protocol: FSK_PULSE_PCM, chip ≈ 58 µs, 10 payload bytes.
    Byte layout after sync:
      [type:8=0x43][id:24]
      [bat_msb:1][pm25_hi:6:+1pad][pm25_lo:8]
      [bat_lsb:2][pm10_hi:6][pm10_lo:8]
      [crc8:8][xor_chk:8]
    CRC-8: poly 0x31, init 0x00, bytes 0–8.
    Checksum: XOR of bytes 0–8 == byte 9.
    """
    name     = "Fine Offset WH43"
    bit_rate = 1_000_000 / 58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 10)
        if data is None or data[0] != 0x43:
            return None
        if crc8(data[:9], 0x31, 0x00) != data[8]:
            return None
        xor = 0
        for b in data[:9]:
            xor ^= b
        if xor != data[9]:
            return None

        device_id = (data[1] << 16) | (data[2] << 8) | data[3]
        bat_msb   = (data[4] >> 6) & 0x01
        pm25_raw  = ((data[4] & 0x3F) << 8) | data[5]
        bat_lsb   = (data[6] >> 6) & 0x03
        pm10_raw  = ((data[6] & 0x3F) << 8) | data[7]
        bat_level = (bat_msb << 2) | bat_lsb   # 0–7; 0 = lowest
        battery_ok = bat_level >= 1

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":                  device_id,
            "battery_ok":          battery_ok,
            "pm2_5_ug_m3":         round(pm25_raw * 0.1, 1),
            "pm10_0_ug_m3":        round(pm10_raw * 0.1, 1),
            "mic":                 "CRC",
        })


__all__ = ["FineOffsetWH43"]
