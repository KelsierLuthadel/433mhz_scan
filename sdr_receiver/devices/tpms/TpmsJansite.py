"""Jansite TPMS TY02S sensor.

Jansite TY02S TPMS decoder.

FSK_PULSE_PCM chip=52 µs Manchester-encoded.
Preamble (inverted): 0xaa 0xaa 0xa9 -> then Manchester decode -> 7 bytes:
  ID (28b) = b[0]<<20 | b[1]<<12 | b[2]<<4 | b[3]>>4
  flags    = b[3] & 0x0F
  pressure = b[4] * 1.7 kPa
  temp     = b[5] - 50 deg C
  b[6]     = checksum (TODO in original)

Source: tpms_jansite.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _pulses_to_chips, _manchester_decode, _bits_to_bytes_n, _find_pattern
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsJansite(RawDecoder):
    """Jansite TPMS TY02S sensor."""

    name    = "Jansite-TY02S"
    _chip_us = 52.0
    _preamble = [1, 0, 1, 0, 1, 0, 1, 0,  # 0xaa
                 1, 0, 1, 0, 1, 0, 1, 0,  # 0xaa
                 1, 0, 1, 0, 1, 0, 0, 1]  # 0xa9

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        chips = _pulses_to_chips(pulses, self._chip_us)
        chips = [1 - c for c in chips]  # invert

        pos = _find_pattern(chips, self._preamble)
        if pos < 0:
            return None
        remaining = chips[pos + len(self._preamble):]

        bits = _manchester_decode(remaining)
        if bits is None or len(bits) < 56:
            return None

        b = _bits_to_bytes_n(bits, 7)
        if b is None:
            return None

        sensor_id    = (b[0] << 20) | (b[1] << 12) | (b[2] << 4) | (b[3] >> 4)
        flags        = b[3] & 0x0F
        pressure_kpa = b[4] * 1.7
        temperature_c = b[5] - 50.0

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:07x}",
            "flags":         flags,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
        })


__all__ = ["TpmsJansite"]
