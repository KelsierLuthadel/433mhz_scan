"""LaCrosse LTV-R1/R3 rainfall gauge, LTV-W1/W2 wind sensor (FSK PCM, 104 µs)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseR1(FSKPCMDecoder):
    """LaCrosse LTV-R1/R3 rainfall gauge, LTV-W1/W2 wind sensor (FSK PCM, 104 µs).

    Preamble: 0xd2 0xaa 0x2d 0xd4.  Payload: 11 bytes.
    CRC-8 poly 0x31 init 0x00 over all 11 bytes (result == 0).
    Variant detected by byte[10]: 0x00 → rain gauge, else → wind.
    """
    name     = "LaCrosse-R1"
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
        battery_ok = not bool(b[3] & 0x08)
        seq        = (b[3] >> 1) & 0x07

        if b[10] == 0x00:
            # LTV-R1: rain gauge  byte 5 is XOR-whitened
            rain_raw = ((b[4] ^ 0xAA) << 8) | b[5]
            return DecodedPacket.from_fields("LaCrosse-LTV-R1", freq_hz, {
                "id": sensor_id, "battery_ok": battery_ok,
                "seq": seq, "rain_raw": rain_raw,
            })
        else:
            # LTV-W1/W2: wind sensor
            wind_raw  = (b[4] << 4) | ((b[5] & 0xF0) >> 4)
            direction = ((b[5] & 0x0F) << 8) | b[6]
            speed_kmh = wind_raw * 0.1
            if direction > 360 or speed_kmh > 200:
                return None
            return DecodedPacket.from_fields("LaCrosse-LTV-W1", freq_hz, {
                "id": sensor_id, "battery_ok": battery_ok, "seq": seq,
                "wind_avg_km_h": round(speed_kmh, 1), "wind_dir_deg": direction,
            })


__all__ = ["LaCrosseR1"]
