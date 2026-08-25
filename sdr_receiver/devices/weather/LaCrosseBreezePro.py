"""LaCrosse Breeze Pro all-in-one weather sensor (FSK PCM, ~107 µs chips)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseBreezePro(FSKPCMDecoder):
    """LaCrosse Breeze Pro all-in-one weather sensor (FSK PCM, ~107 µs chips).

    Preamble: 0xd2 0xaa 0x2d 0xd4.  Payload: 11 bytes.
    Layout: ID:24b FLAGS:4b SEQ:3b ?:1b TEMP:12b HUM:12b WSPD:12b WDIR:12b CHK:8b.
    CRC-8 poly 0x31 init 0x00 over all 11 bytes (residual must be 0).
    Temperature: (raw − 400) × 0.1 °C.  Wind speed: raw × 0.1 km/h.
    """
    name     = "LaCrosse-BreezePro"
    bit_rate = 1e6 / 107.0   # ≈ 9346 bps
    n_bits   = 136

    _PREAMBLE = bytes([0xd2, 0xaa, 0x2d, 0xd4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        off = _find_preamble(bits, self._PREAMBLE)
        if off < 0 or off + 88 > len(bits):
            return None
        b = _extract_bytes(bits, off, 11)

        if crc8(b, poly=0x31, init=0x00) != 0:
            return None

        sensor_id  = (b[0] << 16) | (b[1] << 8) | b[2]
        seq        = (b[3] >> 1) & 0x07
        raw_temp   = (b[4] << 4) | ((b[5] & 0xF0) >> 4)
        humidity   = ((b[5] & 0x0F) << 8) | b[6]
        raw_speed  = (b[7] << 4) | ((b[8] & 0xF0) >> 4)
        direction  = ((b[8] & 0x0F) << 8) | b[9]
        temp_c     = (raw_temp - 400) * 0.1
        speed_kmh  = raw_speed * 0.1

        if not (-40.0 <= temp_c <= 70.0 and 0 <= humidity <= 100
                and 0 <= direction <= 360 and 0 <= speed_kmh <= 200):
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"{sensor_id:06x}", "seq": seq,
            "temperature_C": round(temp_c, 1), "humidity": humidity,
            "wind_avg_km_h": round(speed_kmh, 1), "wind_dir_deg": direction,
        })


__all__ = ["LaCrosseBreezePro"]
