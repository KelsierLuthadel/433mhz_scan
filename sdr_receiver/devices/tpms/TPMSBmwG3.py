"""BMW Gen2 Gen3 TPMS sensor.

Copyright (C) 2024 Bruno OCTAU (ProfBoc75), @Billymazze

BMW Gen2/Gen3 TPMS decoder.

The decoder processes BMW tire pressure monitoring system signals from Gen2 and Gen3
vehicles. It identifies the transmission format as FSK with Differential Manchester
encoding, extracts a 32-bit sensor ID, tire pressure in kilopascals, temperature in
Celsius, and status flags. The implementation distinguishes between generations based
on message length and validates data integrity using CRC-16 checksums.

Source: tpms_bmw_g3.c (or tpms_bmw.c Gen2/Gen3 variant)
Modulation: FSK_PULSE_PCM, chip=52 us
Preamble: 0xcccd (differential Manchester in chip stream)
Gen3=11 bytes (88 bits), Gen2=10 bytes (80 bits)
CRC-16 poly=0x1021 init=0x0000 (result must be 0)
Pressure = (byte - 43) * 2.5 kPa; Temperature = byte - 40 deg C
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
from ._helpers import _diff_manchester_decode, _bits_to_bytes, _find_pattern, _int_to_bits
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSBmwG3(FSKPCMDecoder):
    """BMW Gen2/Gen3 TPMS  FSK/Differential-Manchester, CRC-16."""

    name     = "BMW-TPMS-Gen3"
    bit_rate = 1_000_000.0 / 52
    n_bits   = 200
    freq_hz  = 433.92e6

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        preamble = _int_to_bits(0xCCCD, 16)
        pos = _find_pattern(chips, preamble)
        if pos < 0:
            return None
        pos += 16

        for msg_len in (11, 10):
            n_chips = msg_len * 16
            if pos + n_chips > len(chips):
                continue
            decoded = _diff_manchester_decode(chips[pos : pos + n_chips])
            if len(decoded) < msg_len * 8:
                continue
            b = _bits_to_bytes(decoded[: msg_len * 8])
            if crc16(b, 0x1021, 0x0000) != 0:
                continue

            sid  = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
            pres = round((b[4] - 43) * 2.5, 1)
            temp = b[5] - 40
            fields: dict = {
                "id":            f"{sid:08x}",
                "pressure_kPa":  pres,
                "temperature_C": temp,
                "flags1":        b[6],
                "flags2":        b[7],
            }
            if msg_len == 11:
                fields["flags3"] = b[8]
            model = "BMW-TPMS-Gen3" if msg_len == 11 else "BMW-TPMS-Gen2"
            return DecodedPacket.from_fields(model, self.freq_hz, fields)
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSBmwG3"]
