"""Ambient Weather WH31L / Fine Offset WH57 lightning-strike sensor."""
from __future__ import annotations
from ...dsp import crc8, checksum_sum
from ...packet import DecodedPacket
from ._fineoffset_fsk_base import _FineOffsetFSKBase, _fo_find_payload


class FineOffsetWH31L(_FineOffsetFSKBase):
    """Ambient Weather WH31L / Fine Offset WH57 lightning-strike sensor.

    Protocol: FSK_PULSE_PCM, chip ≈ 56 µs, 9 payload bytes.
    Byte layout after sync 0xAA 0x2D 0xD4:
      [type:8=0x57][state:4][id:20][flags:10][dist:6][strikes:8][crc8:8][chk:8]
    State: 0=reset, 1=interference, 4=noise, 8=strike.
    CRC-8: polynomial 0x31, init 0x00, over bytes 0–7.
    Checksum: sum of bytes 0–8 (mod 256).
    """
    name     = "Fine Offset WH31L"
    bit_rate = 1_000_000 / 56

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = _fo_find_payload(bits, 9)
        if data is None or data[0] != 0x57:
            return None
        if crc8(data[:8], 0x31, 0x00) != data[7]:
            return None
        if checksum_sum(data[:8]) != data[8]:
            return None

        state_val = (data[1] >> 4) & 0x0F
        device_id = ((data[1] & 0x0F) << 16) | (data[2] << 8) | data[3]
        flags     = ((data[4] << 2) | (data[5] >> 6)) & 0x3FF
        bat_bits  = (flags >> 1) & 0x03
        distance  = data[5] & 0x3F
        strikes   = data[6]

        state_map = {0: "reset", 1: "interference", 4: "noise", 8: "strike"}
        state_str = state_map.get(state_val, f"unknown({state_val})")
        battery_ok = bat_bits > 0

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":          device_id,
            "battery_ok":  battery_ok,
            "state":       state_str,
            "distance_km": None if distance == 63 else distance,
            "strikes":     strikes,
            "mic":         "CRC",
        })


__all__ = ["FineOffsetWH31L"]
