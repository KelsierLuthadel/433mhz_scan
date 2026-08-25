"""Schrader Motorcycle TPMS sensor.

Schrader Motorcycle TPMS decoder.

OOK_PULSE_MANCHESTER_ZEROBIT chip=122 µs.
13-bit preamble 0x7ff8 (top 13 bits: 1111111111110).
56 bits (7 bytes) after preamble:
  ID (24b) = ((b[0]&0x03)<<22) | (b[1]<<14) | (b[2]<<6) | (b[3]>>2)
  pressure (10b) = ((b[3]&0x03)<<8) | b[4]  -> * 0.5 kPa
  temperature (8b) = b[5] - 50
  b[6] = CRC-8(poly=0x07, init=0xe0) over b[0:6]

Source: tpms_schrader_motorcycle.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _bits_to_bytes_n
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsSchraderMotorcycle(ManchesterDecoder):
    """Schrader Motorcycle TPMS sensor."""

    name     = "Schrader-Motorcycle"
    chip_us  = 122.0
    reset_us = 375.0
    n_bits   = 56 + 13  # preamble + data

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Find 13-bit preamble: 13 ones followed by 0
        # 0x7ff8 top 13 bits = 1111111111110  (13 bits)
        preamble = [1] * 12 + [0]  # 0x7ff8 >> 3 = 0xFFF, but 13 bits = 1111111111110
        pos = -1
        for i in range(len(bits) - 13 - 56 + 1):
            if bits[i: i + 13] == preamble:
                pos = i + 13
                break
        if pos < 0 or pos + 56 > len(bits):
            return None

        b = _bits_to_bytes_n(bits[pos:], 7)
        if b is None:
            return None

        crc_rx = b[6]
        if crc8(bytes(b[:6]), poly=0x07, init=0xe0) != crc_rx:
            return None

        sensor_id   = (((b[0] & 0x03) << 22) | (b[1] << 14) |
                       (b[2] << 6) | (b[3] >> 2))
        pressure_kpa = (((b[3] & 0x03) << 8) | b[4]) * 0.5
        temperature_c = b[5] - 50.0

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:06x}",
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "mic":           "CRC",
        })


__all__ = ["TpmsSchraderMotorcycle"]
