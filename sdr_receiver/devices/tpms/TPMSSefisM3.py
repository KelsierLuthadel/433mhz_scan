"""Sefis M3 / Careud / Sykik SRTP300 TPMS.

Copyright (C) 2026 Benjamin Larsson

Sefis M3 / Careud / Sykik SRTP300 TPMS decoder.

Uses FSK_PCM modulation at 52 microseconds per bit with Manchester encoding.
Messages contain a preamble, sync word (0x5a9d), and 9-byte payload.
Pressure derives from a 15-bit code combining a "page" prefix and subsequent
bits, converted via formula (code - 0x0e00) / 102.4. Temperature combines
bytes B2 and B5, calculated as 14 plus the lower nibble of their sum.
CRC-16 validation uses polynomial 0x1021 over the first seven payload bytes.

Source: tpms_sefis_m3.c
Modulation: FSK_PULSE_PCM, chip=52 us, reset=5000 us
Sync: 0x66,0x99,0x96,0xa6 (32 bits) then Manchester decode 72 bits (9 bytes)
Payload bytes XOR-inverted (^ 0xFF) after decode
CRC-16 poly=0x1021 init=0x0000 over b[0:7]; result in b[7:9]
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _bits_to_bytes, _find_pattern, _int_to_bits
if TYPE_CHECKING:
    from ...dsp import Pulse


_SYNC = _int_to_bits(0x669996A6, 32)


class TPMSSefisM3(FSKPCMDecoder):
    """Sefis M3 / Careud / Sykik SRTP300 TPMS  FSK/Manchester, CRC-16."""

    name     = "Sefis-M3-TPMS"
    bit_rate = 1_000_000.0 / 52
    n_bits   = 200
    freq_hz  = 433.92e6

    # Sync word as NRZ chips in FSK stream: 0x66, 0x99, 0x96, 0xa6
    _SYNC = _int_to_bits(0x669996A6, 32)

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        sync = self._SYNC
        pos = _find_pattern(chips, sync)
        if pos < 0:
            return None
        pos += 32  # skip sync

        decoded = _mc_decode(chips[pos:], 72)
        if len(decoded) < 72:
            return None
        b = bytearray(_bits_to_bytes(decoded[:72]))
        if len(b) < 9:
            return None
        # Invert all payload bytes
        for i in range(len(b)):
            b[i] ^= 0xFF

        # CRC-16 over first 7 bytes
        crc_calc = crc16(bytes(b[:7]), 0x1021, 0x0000)
        crc_recv = (b[7] << 8) | b[8]
        if crc_calc != crc_recv:
            return None

        # Pressure page decoding
        page_key = b[4] >> 5
        page_map = {7: 0, 4: 1, 5: 2, 2: 3}
        pressure_kpa = None
        if page_key in page_map:
            page = page_map[page_key]
            code = (page << 13) | ((b[4] & 0x1F) << 8) | b[5]
            pres = (code - 0x0E00) / 102.4
            pressure_kpa = round(max(0.0, pres), 0)

        temp_code = (b[2] + b[5]) & 0xFF
        temp_c    = 14 + (temp_code & 0x0F)
        code_str  = "".join(f"{x:02x}" for x in b[:7])

        fields: dict = {
            "code":          code_str,
            "temperature_C": temp_c,
        }
        if pressure_kpa is not None:
            fields["pressure_kPa"] = pressure_kpa
        return DecodedPacket.from_fields("Sefis-M3-TPMS", self.freq_hz, fields)

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSSefisM3"]
