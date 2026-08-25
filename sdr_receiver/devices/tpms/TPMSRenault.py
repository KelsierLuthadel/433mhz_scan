"""FSK 9 byte Manchester encoded TPMS with CRC.

Copyright (C) 2017 Christian W. Zuckschwerdt <zany@triq.net>

Renault TPMS decoder.

Handles FSK 9 byte Manchester encoded TPMS signals detected in Renault and Dacia vehicles.

Vehicles: Renault Clio, Renault Captur, Renault Zoe, and possibly Dacia Sandero.
Packet Structure: 9 bytes containing flags, pressure (10-bit), 24-bit ID,
temperature, unknown data, and CRC-8 checksum.
Pressure: Encoded as 10-bit value * 0.75 kPa
Temperature: Raw value minus 30 deg C offset
Checksum: CRC-8 truncated poly 0x07 init 0x00
Preamble: 55 55 55 56 (inverted to aa aa a9)
Modulation: FSK_PULSE_PCM with 52-sample width

Source: tpms_renault.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _bits_to_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSRenault(FSKPCMDecoder):
    """Renault TPMS  FSK/Manchester, CRC-8."""

    name     = "Renault-TPMS"
    bit_rate = 1_000_000.0 / 52
    n_bits   = 200
    freq_hz  = 433.92e6

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        for offset in range(min(32, len(chips))):
            decoded = _mc_decode(chips[offset:], 160)
            if len(decoded) < 72:
                continue
            b = _bits_to_bytes(decoded[:72])
            if len(b) < 9:
                continue
            if crc8(b[:8], 0x07, 0x00) != b[8]:
                continue

            flags       = b[0] >> 2
            sid         = (b[5] << 16) | (b[4] << 8) | b[3]
            pressure_r  = ((b[0] & 0x03) << 8) | b[1]
            pres        = round(pressure_r * 0.75, 1)
            temp        = b[2] - 30

            return DecodedPacket.from_fields("Renault-TPMS", self.freq_hz, {
                "id":            f"{sid:06x}",
                "flags":         f"{flags:02x}",
                "pressure_kPa":  pres,
                "temperature_C": temp,
            })
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSRenault"]
