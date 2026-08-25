"""Porsche Boxster/Cayman TPMS decoder.

Copyright (C) 2021 Christian W. Zuckschwerdt <zany@triq.net>

Porsche Boxster/Cayman (Typ 987) TPMS decoder.

Encoding: Differential Manchester Coded (DMC)
Preamble: {30}ccccccca (33333332)
Data Structure: 80-bit packet containing ID, pressure, temperature, status flags,
and CRC-16 checksum.
Calculations:
  Pressure: scale 2.5 offset -100 kPa
  Temperature: offset -40 deg C
Validation: CRC-16 polynomial 0x1021, initial value 0xffff over 10 bytes
Modulation: FSK Pulse PCM with 52-sample width

Source: tpms_porsche.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
from ._helpers import _diff_manchester_decode, _bits_to_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSPorsche(FSKPCMDecoder):
    """Porsche Boxster/Cayman TPMS  FSK/Differential-Manchester, CRC-16."""

    name     = "Porsche-TPMS"
    bit_rate = 1_000_000.0 / 52
    n_bits   = 200
    freq_hz  = 433.92e6

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        for offset in range(min(32, len(chips))):
            decoded = _diff_manchester_decode(chips[offset:])
            if len(decoded) < 80:
                continue
            b = _bits_to_bytes(decoded[:80])
            if len(b) < 10:
                continue
            if crc16(b, 0x1021, 0xFFFF) != 0:
                continue

            sid   = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
            pres  = round(b[4] * 5 / 2 - 100, 1)
            temp  = b[5] - 40
            flags = (b[6] << 8) | b[7]

            return DecodedPacket.from_fields("Porsche-TPMS", self.freq_hz, {
                "id":            f"{sid:08x}",
                "pressure_kPa":  pres,
                "temperature_C": temp,
                "flags":         f"{flags:04x}",
            })
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSPorsche"]
