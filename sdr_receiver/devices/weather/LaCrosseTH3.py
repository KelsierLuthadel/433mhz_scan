"""LaCrosse LTV-TH2 / LTV-TH3 temperature+humidity (FSK PCM, ~104 µs chips)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseTH3(FSKPCMDecoder):
    """LaCrosse LTV-TH2 / LTV-TH3 temperature+humidity (FSK PCM, ~104 µs chips).

    Preamble: 0xd2 0xaa 0x2d 0xd4  (32 bits).
    Payload (8 bytes): ID:24b FLAGS:4b SEQ:3b ?:1b TEMP:12b HUM:12b CRC:8b.
    CRC-8 poly 0x31 init 0x00 over first 7 bytes.
    Temperature: (raw − 400) × 0.1 °C.
    """
    name     = "LaCrosse-TH3"
    bit_rate = 1e6 / 104.0   # ≈ 9615 bps
    n_bits   = 120            # preamble(32) + payload(64) + margin(24)

    _PREAMBLE = bytes([0xd2, 0xaa, 0x2d, 0xd4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        off = _find_preamble(bits, self._PREAMBLE)
        if off < 0 or off + 64 > len(bits):
            return None
        b = _extract_bytes(bits, off, 8)

        if crc8(b[:7], poly=0x31, init=0x00) != b[7]:
            return None

        sensor_id  = (b[0] << 16) | (b[1] << 8) | b[2]
        battery_ok = not bool(b[3] & 0x08)
        seq        = (b[3] >> 1) & 0x07
        temp_raw   = (b[4] << 4) | (b[5] >> 4)
        humidity   = ((b[5] & 0x0F) << 8) | b[6]
        temp_c     = (temp_raw - 400) * 0.1

        if not -40.0 <= temp_c <= 80.0 or not 0 <= humidity <= 100:
            return None

        return DecodedPacket.from_fields("LaCrosse-LTV-TH3", freq_hz, {
            "id": sensor_id, "battery_ok": battery_ok, "seq": seq,
            "temperature_C": round(temp_c, 1), "humidity": humidity,
        })


__all__ = ["LaCrosseTH3"]
