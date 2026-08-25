"""Jansite TPMS TY588-EU2 sensor.

Jansite TY588-EU2 TPMS decoder.

FSK_PULSE_PCM chip=51 µs Manchester manual decode.
44 raw preamble bits: 99aa5a6a9aa, then 128 Manchester chips -> 8 bytes.
Validation:
  B7 == B0
  (B3 + B4) & 0xff == 0x30
  (B0 & 0x0f) == (B1 & 0x0f)
temp_C   = ((B2 + B5) & 0xff) - 139
pres_kPa = (((B5 + B6) & 0xff) - 90) * 2.5

Source: tpms_jansite_ty588.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _pulses_to_chips, _manchester_decode, _bits_to_bytes_n, _find_pattern
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsJansiteTy588(RawDecoder):
    """Jansite TPMS TY588-EU2 sensor."""

    name    = "Jansite-TY588"
    _chip_us = 51.0
    # Preamble pattern as bit list for 0x9,0x9,0xa,0xa,0x5,0xa,0x6,0xa,0x9,0xa,0xa
    # Simplified to search for the 0xaa Manchester preamble then 0x5a sync
    _preamble_bytes = bytes([0xaa, 0xaa, 0x5a])

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        chips = _pulses_to_chips(pulses, self._chip_us)

        # Build preamble chip pattern
        preamble: list[int] = []
        for byte in self._preamble_bytes:
            for bit_idx in range(7, -1, -1):
                preamble.append((byte >> bit_idx) & 1)

        pos = _find_pattern(chips, preamble)
        if pos < 0:
            return None
        remaining = chips[pos + len(preamble):]

        data_bits = _manchester_decode(remaining)
        if data_bits is None or len(data_bits) < 64:
            return None

        b = _bits_to_bytes_n(data_bits, 8)
        if b is None:
            return None

        if b[7] != b[0]:
            return None
        if (b[0] & 0x0F) != (b[1] & 0x0F):
            return None
        if ((b[3] + b[4]) & 0xFF) != 0x30:
            return None

        temperature_c = ((b[2] + b[5]) & 0xFF) - 139.0
        pressure_kpa  = (((b[5] + b[6]) & 0xFF) - 90) * 2.5

        if not (-40 <= temperature_c <= 120):
            return None
        if pressure_kpa < 0:
            return None

        code = b[:7].hex().upper()
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "code":          code,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "mic":           "CHECKSUM",
        })


__all__ = ["TpmsJansiteTy588"]
