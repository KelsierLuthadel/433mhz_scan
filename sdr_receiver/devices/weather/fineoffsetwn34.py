"""Fine Offset WN34S/L/D, WN38, Froggit DP150/D35 temperature sensor."""
from __future__ import annotations
from ...dsp import crc8, checksum_sum
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWN34(_FineOffsetFSKBase):
    """Fine Offset WN34S/L/D, WN38, Froggit DP150/D35 temperature sensor.

    Protocol: FSK_PULSE_PCM, chip ≈ 58 µs, 9 payload bytes.
    Family codes: 0x34 (WN34) or 0x38 (WN38).
    Byte layout after sync:
      [type:8][id:24]
      byte4: [sub_type:4][temp_hi:4]
      byte5: temp_lo:8  → temp_raw = ((byte4 & 0x0F) << 8) | byte5
      byte6: battery raw (7 bits; mv = raw × 20)
      byte7: CRC-8 (poly 0x31, bytes 0–6)
      byte8: additive checksum (sum bytes 0–7)
    Temperature: temp_raw / 10.0 − 40.0 °C (sub_type != 4).
    """
    name     = "Fine Offset WN34"
    bit_rate = 1_000_000 / 58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 9)
        if data is None or data[0] not in (0x34, 0x38):
            return None
        if crc8(data[:7], 0x31, 0x00) != data[7]:
            return None
        if checksum_sum(data[:8]) != data[8]:
            return None

        family    = data[0]
        device_id = (data[1] << 16) | (data[2] << 8) | data[3]
        sub_type  = (data[4] >> 4) & 0x0F
        temp_raw  = ((data[4] & 0x0F) << 8) | data[5]
        temp_c    = temp_raw / 10.0 - 40.0
        bat_raw   = data[6] & 0x7F
        bat_mv    = bat_raw * 20
        battery_ok = bat_mv >= 2300

        model = "Fine Offset WN38" if family == 0x38 else "Fine Offset WN34"
        if not -40.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(model, freq_hz, {
            "id":            device_id,
            "sub_type":      sub_type,
            "battery_ok":    battery_ok,
            "battery_mV":    bat_mv,
            "temperature_C": round(temp_c, 1),
            "mic":           "CRC",
        })


__all__ = ["FineOffsetWN34"]
