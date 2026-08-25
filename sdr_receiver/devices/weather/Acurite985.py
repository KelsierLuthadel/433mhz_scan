"""Acurite 985 Dual Refrigerator/Freezer Thermometer."""
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


class Acurite985(OOKPPMDecoder):
    """Acurite 985 Dual Refrigerator/Freezer Thermometer.

    r_device: OOK_PULSE_PPM, short=556, long=1104, reset=7636.
    Message: 56 bits (7 bytes), LSB-first within each byte.
    Layout after bit-reversal:
      b[0..1]    = sync bytes (ignored)
      b[2]       = temp (signed magnitude, °F; bit 7 = sign)
      b[3..4]    = sensor ID (16 bits)
      b[5]       = status (bit 0: sensor#; bits 1-2: low battery per sensor)
      b[6]       = CRC-8 (poly 0x07) over b[2:6]
    """
    name     = "Acurite-985"
    short_us = 556.0
    long_us  = 1104.0
    reset_us = 7636.0
    n_bits   = 56

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        raw = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 56, 8))
        b   = bytes(_reverse_byte(x) for x in raw)
        if crc8(b[2:6], poly=0x07, init=0x00) != b[6]:
            return None
        temp_f     = -(b[2] & 0x7F) if (b[2] & 0x80) else (b[2] & 0x7F)
        temp_c     = (temp_f - 32.0) * 5.0 / 9.0
        sensor_id  = (b[3] << 8) | b[4]
        status     = b[5]
        sensor_num = 2 if (status & 0x01) else 1
        batt_mask  = 0x02 if sensor_num == 1 else 0x04
        battery_ok = not bool(status & batt_mask)
        if not -40.0 <= temp_f <= 104.0:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       sensor_num,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
            "temperature_F": temp_f,
        })


__all__ = ["Acurite985"]
