"""LaCrosse LTV-WR1 Multi Sensor  wind + rain (FSK PCM, 104 µs chips)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseWR1(FSKPCMDecoder):
    """LaCrosse LTV-WR1 Multi Sensor  wind + rain (FSK PCM, 104 µs chips).

    Preamble: 0xd2 0xaa 0x2d 0xd4.  Payload: 11 bytes.
    Layout: ID:24b FLAGS:4b SEQ:3b ?:1b WSPD:12b WDIR:12b RAIN1:12b RAIN2:12b CHK:8b.
    CRC-8 poly 0x31 init 0x00 over all 11 bytes (residual must be 0).
    """
    name     = "LaCrosse-WR1"
    bit_rate = 1e6 / 104.0
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
        wind_raw   = (b[4] << 4) | ((b[5] & 0xF0) >> 4)
        direction  = ((b[5] & 0x0F) << 8) | b[6]
        rain_raw1  = (b[7] << 4) | ((b[8] & 0xF0) >> 4)
        rain_raw2  = ((b[8] & 0x0F) << 8) | b[9]
        speed_kmh  = wind_raw * 0.1

        if direction > 360 or speed_kmh > 200:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": f"{sensor_id:06x}", "seq": seq,
            "wind_avg_km_h": round(speed_kmh, 1), "wind_dir_deg": direction,
            "rain_raw1": rain_raw1, "rain_raw2": rain_raw2,
        })


__all__ = ["LaCrosseWR1"]
