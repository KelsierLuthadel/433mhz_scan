"""FSK 9 byte Manchester encoded TPMS with CRC.

Copyright (C) 2017 Christian W. Zuckschwerdt <zany@triq.net>

Renault 0435R TPMS decoder.

Handles Renault 0435R TPMS variant with inverted preamble 0xaaa9 (16 bits)
then Manchester-decode 9 bytes. Checksum: XOR of all 9 bytes = 0.
Pressure = b[4] / 0.75 kPa; Temperature = b[5] - 50 deg C
b[6] = centrifugal acceleration (raw * 5 m/s^2)
b[8] bits: lower=tick counter, MSB=active status

Source: tpms_renault.c
Modulation: FSK_PULSE_PCM, chip=52 us
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _bits_to_bytes, _find_pattern, _int_to_bits, _xor_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSRenault0435R(FSKPCMDecoder):
    """Renault 0435R TPMS  FSK/Manchester, XOR checksum."""

    name     = "Renault-0435R-TPMS"
    bit_rate = 1_000_000.0 / 52
    n_bits   = 200
    freq_hz  = 433.92e6

    # Preamble in NRZ chip stream (inverted 0xaaa9)
    _PREAMBLE = _int_to_bits(0xaaa9 ^ 0xFFFF, 16)  # inverted pattern

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        # Try both the inverted and normal preamble positions
        for preamble in (_int_to_bits(0x5556, 16), _int_to_bits(0xaaa9, 16)):
            pos = _find_pattern(chips, preamble)
            if pos < 0:
                continue
            pos += 16
            decoded = _mc_decode(chips[pos:], 72)
            if len(decoded) < 72:
                continue
            b = _bits_to_bytes(decoded[:72])
            if len(b) < 9:
                continue
            if _xor_bytes(b[:9]) != 0:
                continue

            sid   = (b[2] << 16) | (b[1] << 8) | b[0]
            flags = b[3]
            pres  = round(b[4] / 0.75, 1)
            temp  = b[5] - 50
            accel = b[6] * 5
            tick  = b[8] & 0x7F
            active = bool(b[8] & 0x80)

            return DecodedPacket.from_fields("Renault-0435R-TPMS", self.freq_hz, {
                "id":             f"{sid:06x}",
                "flags":          f"{flags:02x}",
                "pressure_kPa":   pres,
                "temperature_C":  temp,
                "accel_ms2":      accel,
                "tick":           tick,
                "active":         active,
            })
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSRenault0435R"]
