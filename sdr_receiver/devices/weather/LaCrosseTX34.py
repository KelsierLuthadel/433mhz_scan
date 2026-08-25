"""LaCrosse TX34-IT rain gauge (FSK PCM, ~58 µs chips, 40-bit payload)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseTX34(FSKPCMDecoder):
    """LaCrosse TX34-IT rain gauge (FSK PCM, ~58 µs chips, 40-bit payload).

    Preamble: 0xa2 0xdd 0x40.
    Payload (5 bytes): model(4b)+id_hi(4b)  id_lo(2b)+batt(2b)+?(2b)
                       rain_hi(8b)  rain_lo(8b)  CRC(8b).
    CRC-8 poly 0x31 init 0x00 over first 4 bytes.
    Rain: raw × 0.222 mm.
    """
    name     = "LaCrosse-TX34"
    bit_rate = 1e6 / 58.0    # ≈ 17241 bps
    n_bits   = 64

    _PREAMBLE = bytes([0xa2, 0xdd, 0x40])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        off = _find_preamble(bits, self._PREAMBLE)
        if off < 0 or off + 40 > len(bits):
            return None
        b = _extract_bytes(bits, off, 5)

        if crc8(b[:4], poly=0x31, init=0x00) != b[4]:
            return None

        model_marker = (b[0] >> 4) & 0xF
        if model_marker != 5:  # Rain-gauge model ID
            return None

        sensor_id  = ((b[0] & 0x0F) << 2) | ((b[1] >> 6) & 0x03)
        battery_ok = not bool((b[1] >> 4) & 0x3)
        rain_raw   = (b[2] << 8) | b[3]
        rain_mm    = rain_raw * 0.222

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": sensor_id, "battery_ok": battery_ok,
            "rain_mm": round(rain_mm, 1),
        })


__all__ = ["LaCrosseTX34"]
