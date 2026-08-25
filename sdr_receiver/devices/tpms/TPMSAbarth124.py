"""VDO TPMS Type TG1C and Q85.

Copyright (C) TTigges for (VDO Type TG1C via) Abarth 124 Spider TPMS decoded.
Protocol similar (and based on) Jansite Solar TPMS by Andreas Spiess and
Christian W. Zuckschwerdt.
Copyright (C) 2024 Bruno OCTAU (ProfBoc75) Add Shenzhen EGQ Q85 support.

VDO TPMS Type TG1C and Q85 decoder.

Supports two tire pressure monitoring systems. The TG1C variant, found in vehicles
like the Abarth 124 Spider and certain Mazda models, transmits 9-byte
Manchester-encoded messages with XOR checksums. The Q85 variant from Shenzhen EGQ
operates on 12-byte encoded frames with both checksum and CRC-16 verification.
Both operate at 433.92 MHz with distinct pressure calibrations (1.38 kPa multiplier
for TG1C, 3.0 for Q85) and temperature offsets (50 deg C and 55 deg C respectively).

Source: tpms_abarth124.c
Modulation: FSK_PULSE_PCM, chip=52 us
TG1C (Abarth 124): 72-bit Manchester payload, XOR bytes 0-8 = 0
Q85 (Shenzhen EGQ): 96-bit Manchester payload, XOR + CRC-16 poly=0x1021 init=0xffff
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _bits_to_bytes, _xor_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSAbarth124(FSKPCMDecoder):
    """Abarth 124 Spider and Shenzhen EGQ Q85 TPMS  FSK/Manchester."""

    name     = "Abarth124-TPMS"
    bit_rate = 1_000_000.0 / 52
    n_bits   = 200
    freq_hz  = 433.92e6

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        # Try TG1C first (72-bit / 9-byte payload), then Q85 (96-bit / 12-byte)
        for offset in range(min(32, len(chips))):
            # --- TG1C (Abarth 124 Spider) ---
            dec = _mc_decode(chips[offset:], 72)
            if len(dec) >= 72:
                b = _bits_to_bytes(dec[:72])
                if len(b) >= 9 and _xor_bytes(b[:9]) == 0:
                    temp_c = b[6] - 50
                    if -50 <= temp_c <= 125:
                        sid  = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
                        pres = round(b[5] * 1.38, 0)
                        return DecodedPacket.from_fields("Abarth-124-TPMS", self.freq_hz, {
                            "id":            f"{sid:08x}",
                            "flags":         f"{b[4]:02x}",
                            "pressure_kPa":  pres,
                            "temperature_C": temp_c,
                            "status":        b[7],
                        })

            # --- Q85 (Shenzhen EGQ Q85) ---
            dec = _mc_decode(chips[offset:], 96)
            if len(dec) >= 96:
                b = _bits_to_bytes(dec[:96])
                if len(b) >= 12 and _xor_bytes(b[:9]) == 0:
                    crc_le = (b[11] << 8) | b[10]
                    if crc16(b[:10], 0x1021, 0xFFFF) == crc_le:
                        temp_c = b[6] - 55
                        if -20 <= temp_c <= 80:
                            sid  = (b[0] << 24) | (b[1] << 16) | (b[2] << 8) | b[3]
                            pres = round(b[5] * 3.0, 0)
                            return DecodedPacket.from_fields("Shenzhen-EGQQ85-TPMS", self.freq_hz, {
                                "id":            f"{sid:08x}",
                                "flags":         f"{b[4]:02x}",
                                "pressure_kPa":  pres,
                                "temperature_C": temp_c,
                                "status":        b[7],
                            })
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSAbarth124"]
