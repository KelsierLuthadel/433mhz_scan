"""Jansite TPMS TY-468-eu2 sensor.

Jansite TY-468-eu2 TPMS decoder.

OOK_PULSE_PCM chip=50 µs Manchester manual decode.
Same physical structure as iMars T240:
  32-bit preamble 0xaaaaaaaa + 128 chips -> Manchester -> 8 bytes.
Validation:
  B7 == B0
  (B0 & 0x0f) == (B1 & 0x0f)
  checksum = (B3 + B4) & 0xff -> selects calibration constants.
Known calibration:
  cksum=0xfb: temp_offset=224, pres_offset=273
  cksum=0x64: temp_offset=153, pres_offset=201
temp_C = temp_offset - ((B2 + B5) & 0xff)
pres_kPa = (pres_offset - ((B5 + B6) & 0xff)) * 2.5

Source: tpms_jansite_ty468.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _manchester_decode, _bits_to_bytes_n
if TYPE_CHECKING:
    from ...dsp import Pulse


_TY468_CAL = {
    0xFB: (224, 273),
    0x64: (153, 201),
}


class TpmsJansiteTy468(OOKPCMDecoder):
    """Jansite TPMS TY-468-eu2 sensor."""

    name     = "Jansite-TY468"
    chip_us  = 50.0
    reset_us = 200.0
    n_bits   = 160  # 32 preamble + 128 data chips

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        preamble = [1, 0] * 16
        pos = -1
        for i in range(len(bits) - 160 + 1):
            if bits[i: i + 32] == preamble:
                pos = i + 32
                break
        if pos < 0 or pos + 128 > len(bits):
            return None

        data_bits = _manchester_decode(bits[pos: pos + 128])
        if data_bits is None or len(data_bits) < 64:
            return None

        b = _bits_to_bytes_n(data_bits, 8)
        if b is None:
            return None

        if b[7] != b[0]:
            return None
        if (b[0] & 0x0F) != (b[1] & 0x0F):
            return None

        checksum = (b[3] + b[4]) & 0xFF
        if checksum not in _TY468_CAL:
            return None

        temp_off, pres_off = _TY468_CAL[checksum]
        temperature_c = temp_off - ((b[2] + b[5]) & 0xFF)
        pressure_kpa  = (pres_off - ((b[5] + b[6]) & 0xFF)) * 2.5

        if pressure_kpa < 0:
            return None

        code = b[:7].hex().upper()
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "code":          code,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "mic":           "CHECKSUM",
        })


__all__ = ["TpmsJansiteTy468"]
