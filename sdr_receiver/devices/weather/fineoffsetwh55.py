"""Fine Offset / Ecowitt WH55 water leak sensor."""
from __future__ import annotations
from ...dsp import crc8
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWH55(_FineOffsetFSKBase):
    """Fine Offset / Ecowitt WH55 water leak sensor.

    Protocol: FSK_PULSE_PCM, chip ≈ 60 µs, 9 payload bytes.
    Preamble: 0xAA 0x2D 0xD4 (standard), first payload byte = 0x55.
    Byte layout:
      [type:8=0x55]
      byte1: [channel:4][flags:4]
      bytes2-3: device ID (16-bit)
      byte4: battery level (0x01–0x05 → 20–100%)
      bytes5-6: raw sensor value (16-bit big-endian)
      byte7: [alarm:1][sensitivity:1][reserved:6]
      byte8: CRC-8 (poly 0x31, bytes 0–7)
    """
    name     = "Fine Offset WH55"
    bit_rate = 1_000_000 / 60

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 9)
        if data is None or data[0] != 0x55:
            return None
        if crc8(data[:8], 0x31, 0x00) != data[8]:
            return None

        channel   = (data[1] >> 4) & 0x0F
        device_id = (data[2] << 8) | data[3]
        bat_raw   = data[4]
        raw_val   = (data[5] << 8) | data[6]
        alarm     = bool((data[7] >> 7) & 1)
        sensitivity = bool((data[7] >> 6) & 1)
        bat_pct   = min(100, bat_raw * 20) if 1 <= bat_raw <= 5 else 0
        battery_ok = bat_raw >= 1

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":          device_id,
            "channel":     channel,
            "battery_ok":  battery_ok,
            "battery_pct": bat_pct,
            "raw_value":   raw_val,
            "alarm":       alarm,
            "sensitivity": sensitivity,
            "mic":         "CRC",
        })


__all__ = ["FineOffsetWH55"]
