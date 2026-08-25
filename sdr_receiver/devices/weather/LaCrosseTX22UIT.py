"""LaCrosse TX22U-IT multi-sensor transmitter (FSK PCM, ~116 µs chips)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseTX22UIT(FSKPCMDecoder):
    """LaCrosse TX22U-IT multi-sensor transmitter (FSK PCM, ~116 µs chips).

    Preamble: 0xaa 0xaa 0x2d 0xd4.
    Payload: ID(1B) FLAGS(1B) + 1-5 quartets × 2B + CRC(1B).
    Quartet types: 0=temp, 1=hum, 2=rain, 3=wind_avg+dir, 4=wind_gust.
    CRC-8 poly 0x31 init 0x00 over all bytes preceding CRC.
    """
    name     = "LaCrosse-TX22UIT"
    bit_rate = 1e6 / 116.0   # ≈ 8621 bps
    n_bits   = 96

    _PREAMBLE = bytes([0xaa, 0xaa, 0x2d, 0xd4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        off = _find_preamble(bits, self._PREAMBLE)
        if off < 0:
            return None
        avail = (len(bits) - off) // 8
        if avail < 3:
            return None
        b = _extract_bytes(bits, off, min(avail, 14))

        for n_q in range(1, 6):
            total = 2 + n_q * 2 + 1
            if total > len(b):
                break
            if crc8(b[:total - 1], poly=0x31, init=0x00) != b[total - 1]:
                continue
            result = self._decode_quartets(b, n_q, freq_hz)
            if result is not None:
                return result
        return None

    def _decode_quartets(self, b: bytes, n_q: int, freq_hz: float) -> DecodedPacket | None:
        sensor_id  = b[0]
        battery_ok = not bool(b[1] & 0x08)
        fields: dict = {"id": sensor_id, "battery_ok": battery_ok}
        recognized = 0

        for i in range(n_q):
            q_type = (b[2 + i * 2] >> 4) & 0xF
            nib1   =  b[2 + i * 2] & 0xF
            nib2   = (b[3 + i * 2] >> 4) & 0xF
            nib3   =  b[3 + i * 2] & 0xF

            if q_type == 0:
                temp_c = 10 * nib1 + nib2 + 0.1 * nib3 - 40.0
                fields["temperature_C"] = round(temp_c, 1)
                recognized += 1
            elif q_type == 1:
                fields["humidity"] = 100 * nib1 + 10 * nib2 + nib3
                recognized += 1
            elif q_type == 2:
                fields["rain_raw"] = (nib1 << 8) | (nib2 << 4) | nib3
                recognized += 1
            elif q_type == 3:
                fields["wind_dir_deg"]  = nib1 * 22.5
                fields["wind_avg_km_h"] = round(((nib2 << 4) | nib3) * 0.1 * 3.6, 1)
                recognized += 1
            elif q_type == 4:
                fields["wind_max_km_h"] = round(((nib2 << 4) | nib3) * 0.1 * 3.6, 1)
                recognized += 1

        if recognized == 0:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["LaCrosseTX22UIT"]
