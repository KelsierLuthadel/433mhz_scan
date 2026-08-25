"""BMW Gen4 Gen5 TPMS and Audi TPMS Pressure Alert sensor decoder.

Copyright (C) 2024 Bruno OCTAU (ProfBoc75), @petrjac, @Gucioo,
Christian W. Zuckschwerdt

BMW Gen4/Gen5 and Audi TPMS decoder.

Supported Brands:
- HUF/Beru (0x03)
- Schrader/Sensata (0x23)
- Continental (0x80)
- Audi (0x00, 0x88)

Signal Structure:
- Preamble: 0xaa59
- Manchester-coded payload
- 11 bytes (BMW) or 8 bytes (Audi Pressure Alert)
- CRC-8 validation (polynomial 0x2f, init 0xaa)

Decoded Parameters:
- Sensor ID (32-bit)
- Pressure: b[5] * 2.45 kPa
- Temperature: b[6] - 52 C
- Status flags and nominal pressure (BMW only)

Source: tpms_bmw.c
Modulation: FSK_PULSE_PCM, chip=25 us
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _bits_to_bytes, _find_pattern, _int_to_bits
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSBmw(FSKPCMDecoder):
    """BMW Gen4/Gen5 and Audi TPMS  FSK/Manchester, CRC-8."""

    name     = "BMW-TPMS"
    bit_rate = 1_000_000.0 / 25   # 40 000 chip/s
    n_bits   = 200                 # minimum chips (sanity only)
    freq_hz  = 433.92e6

    _BRAND = {
        0x00: "Audi-Alert",
        0x03: "HUF",
        0x23: "Schrader",
        0x80: "Continental",
        0x88: "Audi",
    }

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        preamble = _int_to_bits(0xaa59, 16)
        pos = _find_pattern(chips, preamble)
        if pos < 0:
            return None
        pos += 16  # advance past preamble chips

        for msg_len in (11, 8):
            n_chips = msg_len * 16  # each data bit = 2 chips (Manchester)
            if pos + n_chips > len(chips):
                continue
            decoded = _mc_decode(chips[pos : pos + n_chips], msg_len * 8)
            if len(decoded) < msg_len * 8:
                continue
            # rtl_433 applies MC_ZEROBIT inversion after decode
            decoded = [b ^ 1 for b in decoded]
            raw_bytes = _bits_to_bytes(decoded[: msg_len * 8])
            if len(raw_bytes) < msg_len:
                continue
            if crc8(raw_bytes, 0x2F, 0xAA) != 0:
                continue

            brand   = raw_bytes[0]
            sid     = bits_to_int(decoded[8:40])
            pres    = round(raw_bytes[5] * 2.45, 1)
            temp    = raw_bytes[6] - 52
            model   = "BMW-TPMS" if msg_len == 11 else "Audi-TPMS-Alert"
            fields: dict = {
                "brand":        self._BRAND.get(brand, f"0x{brand:02x}"),
                "id":           f"{sid:08x}",
                "pressure_kPa": pres,
                "temperature_C": temp,
            }
            if msg_len == 11:
                fields["flags1"] = raw_bytes[7]
                fields["flags2"] = raw_bytes[8]
                fields["flags3"] = raw_bytes[9]
            return DecodedPacket.from_fields(model, self.freq_hz, fields)
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSBmw"]
