"""Fine Offset / Ecowitt WH52 soil moisture, temperature, and EC sensor."""
from __future__ import annotations
from ...dsp import crc8, checksum_sum
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWH52(_FineOffsetFSKBase):
    """Fine Offset / Ecowitt WH52 soil moisture, temperature, and EC sensor.

    Protocol: FSK_PULSE_PCM, chip ≈ 58 µs, 24 payload bytes.
    Family code: 0xA2.
    Byte layout after sync:
      [type:8=0xA2][id:24]
      bytes4-5: temperature (11-bit; (raw/10.0)−40.0 °C)
      byte6: soil moisture (%)
      byte7: unknown
      bytes8-10: electrical conductivity (20-bit, µS/cm)
      … (bytes 11–21 reserved / unknown)
      byte22: CRC-8 (poly 0x31, bytes 0–21)
      byte23: additive checksum (sum bytes 0–22)
    """
    name     = "Fine Offset WH52"
    bit_rate = 1_000_000 / 58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 24)
        if data is None or data[0] != 0xA2:
            return None
        if crc8(data[:22], 0x31, 0x00) != data[22]:
            return None
        if checksum_sum(data[:23]) != data[23]:
            return None

        device_id = (data[1] << 16) | (data[2] << 8) | data[3]
        temp_raw  = ((data[4] & 0x07) << 8) | data[5]
        temp_c    = temp_raw / 10.0 - 40.0
        moisture  = data[6]
        ec_raw    = ((data[8] & 0x0F) << 16) | (data[9] << 8) | data[10]

        bat_raw   = (data[4] >> 4) & 0x07
        battery_ok = bat_raw >= 1

        if not -40.0 <= temp_c <= 80.0:
            return None
        if not 0 <= moisture <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
            "moisture_pct":  moisture,
            "conductivity_uS_cm": ec_raw,
            "mic":           "CRC",
        })


__all__ = ["FineOffsetWH52"]
