"""Inovalley KW9015B rain and temperature sensor decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _bits_to_bytes(bits: list[int]) -> bytearray:
    """Pack MSB-first bits into a bytearray (zero-pad last byte)."""
    n = (len(bits) + 7) // 8
    result = bytearray(n)
    for i, b in enumerate(bits):
        if b:
            result[i >> 3] |= 0x80 >> (i & 7)
    return result


def _nibble_sum(data: bytes | bytearray, n: int) -> int:
    """Sum both nibbles of the first *n* bytes of *data*, return lower 4 bits."""
    total = 0
    for i in range(min(n, len(data))):
        total += (data[i] >> 4) + (data[i] & 0xF)
    return total & 0xF


class InoValleyKW9015B(OOKPPMDecoder):
    """Inovalley KW9015B rain + temperature sensor.

    OOK_PULSE_PPM, short=2000 µs, long=4000 µs, reset=10000 µs.
    36 bits: id[4] | unk[2] | rain[12] | battery[1] | powerup[1] | temp[12] | chk[4].
    Temperature: signed 12-bit, /10 → °C.  Rain: count × 0.45 mm/tip.
    Checksum: nibble sum of bytes 0-3 (lower 4 bits == chk).
    """
    name     = "Inovalley-KW9015B"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 10000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        device_id = bits_to_int(bits[0:4])
        rain_raw  = bits_to_int(bits[6:18])
        battery   = bits[18]
        power_up  = bits[19]
        temp_raw  = bits_to_int(bits[20:32])
        chk_rx    = bits_to_int(bits[32:36])
        b = _bits_to_bytes(bits[:32])
        chk_exp = _nibble_sum(b, 4)
        if chk_rx != chk_exp:
            return None
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c  = temp_raw / 10.0
        rain_mm = rain_raw * 0.45
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           device_id,
            "temperature_C": round(temp_c, 1),
            "rain_mm":       round(rain_mm, 2),
            "battery_ok":    int(not battery),
            "power_up":      power_up,
        })


__all__ = ["InoValleyKW9015B"]
