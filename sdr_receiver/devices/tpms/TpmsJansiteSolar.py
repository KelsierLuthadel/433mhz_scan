"""Jansite TPMS Solar sensor.

Jansite Solar TPMS decoder.

FSK_PULSE_PCM chip=51 µs Manchester-encoded.
Preamble: 0xa6 0xa6 0x5a -> Manchester decode -> 11 bytes:
  B0-B1: sync 0xdd33  (validate)
  B2-B4: 24-bit ID
  B5:    flags
  B6:    temperature raw (-55 deg C)
  B7:    pressure raw (* 1.6 kPa)
  B8:    unknown
  B9-B10: CRC-16/BUYPASS over B2-B8 (poly=0x8005, init=0, no reflection)

Source: tpms_jansite_solar.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
from ._helpers import _pulses_to_chips, _manchester_decode, _bits_to_bytes_n, _find_pattern
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsJansiteSolar(RawDecoder):
    """Jansite TPMS Solar sensor."""

    name    = "Jansite-Solar"
    _chip_us = 51.0
    _preamble_bytes = bytes([0xa6, 0xa6, 0x5a])

    def _preamble_chips(self) -> list[int]:
        chips: list[int] = []
        for byte in self._preamble_bytes:
            for bit_idx in range(7, -1, -1):
                chips.append((byte >> bit_idx) & 1)
        return chips

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        chips = _pulses_to_chips(pulses, self._chip_us)
        preamble = self._preamble_chips()

        pos = _find_pattern(chips, preamble)
        if pos < 0:
            return None
        remaining = chips[pos + len(preamble):]

        bits = _manchester_decode(remaining)
        if bits is None or len(bits) < 88:
            return None

        b = _bits_to_bytes_n(bits, 11)
        if b is None:
            return None

        # Validate sync word
        if b[0] != 0xdd or b[1] != 0x33:
            return None

        # CRC-16/BUYPASS (poly=0x8005, init=0x0000, no reflection)
        crc_rx   = (b[9] << 8) | b[10]
        crc_calc = crc16(b[2:9], poly=0x8005, init=0x0000, ref_in=False, ref_out=False)
        if crc_calc != crc_rx:
            return None

        sensor_id    = (b[2] << 16) | (b[3] << 8) | b[4]
        flags        = b[5]
        temperature_c = b[6] - 55.0
        pressure_kpa  = b[7] * 1.6

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:06x}",
            "flags":         flags,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "mic":           "CRC",
        })


__all__ = ["TpmsJansiteSolar"]
