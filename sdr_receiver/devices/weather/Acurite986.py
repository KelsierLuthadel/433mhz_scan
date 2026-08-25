"""Acurite 986 Refrigerator/Freezer Thermometer."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _reverse_byte(b: int) -> int:
    """Reverse all 8 bits in a byte (LSB-first → MSB-first)."""
    b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
    b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
    b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
    return b


class Acurite986(OOKPPMDecoder):
    """Acurite 986 Refrigerator/Freezer Thermometer.

    r_device: OOK_PULSE_PPM, short=520, long=880, reset=4000.
    Message: 40 bits (5 bytes), LSB-first within each byte.
    Layout after bit-reversal:
      b[0]       = temp (signed magnitude, °F; bit 7 = sign)
      b[1..2]    = sensor ID (16 bits)
      b[3]       = status (bit 0: 1=Freezer, 0=Fridge; bit 1=low battery)
      b[4]       = CRC-8 (poly 0x07) over b[0:4]
    """
    name     = "Acurite-986"
    short_us = 520.0
    long_us  = 880.0
    reset_us = 4000.0
    n_bits   = 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        raw = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8))
        b   = bytes(_reverse_byte(x) for x in raw)
        if crc8(b[:4], poly=0x07, init=0x00) != b[4]:
            return None
        temp_f    = -(b[0] & 0x7F) if (b[0] & 0x80) else (b[0] & 0x7F)
        temp_c    = (temp_f - 32.0) * 5.0 / 9.0
        sensor_id = (b[1] << 8) | b[2]
        status    = b[3]
        channel   = 2 if (status & 0x01) else 1   # 2 = Freezer, 1 = Fridge
        battery_ok = not bool(status & 0x02)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
            "temperature_F": temp_f,
        })


__all__ = ["Acurite986"]
