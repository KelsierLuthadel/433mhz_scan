"""LaCrosse WS6868 weather station  TX232TH and TX231RW (FSK PCM, 58 µs chips)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8, checksum_sum
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseWS6868(FSKPCMDecoder):
    """LaCrosse WS6868 weather station  TX232TH and TX231RW (FSK PCM, 58 µs chips).

    Preamble: 0xd2 0xaa 0x2d 0xd4.
    TX232TH (temp/hum, 8 bytes):  CRC-8 poly 0x31 over 7 bytes.
    TX231RW (wind/rain, 12 bytes): CRC-8 poly 0x31 over 10 bytes +
                                   byte-sum over 11 bytes.
    Header layout: ID:24b BAT:1b TEST:1b CH:2b CTR:3b ?:1b.
    """
    name     = "LaCrosse-WS6868"
    bit_rate = 1e6 / 58.0
    n_bits   = 128

    _PREAMBLE = bytes([0xd2, 0xaa, 0x2d, 0xd4])

    @staticmethod
    def _hdr(b: bytes) -> tuple:
        sensor_id  = (b[0] << 16) | (b[1] << 8) | b[2]
        battery_ok = not bool(b[3] & 0x80)
        test       = bool(b[3] & 0x40)
        channel    = ((b[3] >> 4) & 0x03) + 1
        counter    = b[3] & 0x07
        return sensor_id, battery_ok, test, channel, counter

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        off = _find_preamble(bits, self._PREAMBLE)
        if off < 0:
            return None
        avail = (len(bits) - off) // 8

        # Try TX231RW (12 bytes) first  it needs both CRC and checksum
        if avail >= 12:
            b = _extract_bytes(bits, off, 12)
            if (crc8(b[:10], poly=0x31, init=0x00) == b[10] and
                    checksum_sum(b[:11]) == b[11]):
                sid, bat, test, ch, ctr = self._hdr(b)
                return DecodedPacket.from_fields("LaCrosse-TX231RW", freq_hz, {
                    "id": f"{sid:06x}", "channel": ch, "battery_ok": bat,
                    "test": test, "counter": ctr,
                    "data_raw": b[4:10].hex(),
                })

        # Try TX232TH (8 bytes)
        if avail >= 8:
            b = _extract_bytes(bits, off, 8)
            if crc8(b[:7], poly=0x31, init=0x00) == b[7]:
                sid, bat, test, ch, ctr = self._hdr(b)
                temp_raw = (b[4] << 4) | (b[5] >> 4)
                humidity = ((b[5] & 0x0F) << 8) | b[6]
                temp_c   = (temp_raw - 500) * 0.1
                if not -40.0 <= temp_c <= 80.0 or not 0 <= humidity <= 100:
                    return None
                return DecodedPacket.from_fields("LaCrosse-TX232TH", freq_hz, {
                    "id": f"{sid:06x}", "channel": ch, "battery_ok": bat,
                    "test": test, "counter": ctr,
                    "temperature_C": round(temp_c, 1), "humidity": humidity,
                })

        return None


__all__ = ["LaCrosseWS6868"]
