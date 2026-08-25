"""Hyundai TPMS (VDO) FSK 10 byte Manchester encoded CRC-8 TPMS data.

Copyright (C) 2020 Todor Uzunov aka teou, TTiges, 2019 Andreas Spiess,
2017 Christian W. Zuckschwerdt <zany@triq.net>

Hyundai TPMS (VDO) decoder.

The implementation processes 10-byte Manchester-encoded packets transmitted at
433.92MHz with Continental/VDO sensors (model A2C98607702). Extracts sensor
identification, pressure readings (0-350kPa range), temperature data (offset by
50 deg C), and battery status. Similar protocols are used across multiple
automotive manufacturers including BMW, Fiat-Chrysler-Alfa, Peugeot-Citroen,
Hyundai-KIA, Mitsubishi, and Mazda. Packet validation employs CRC-8 checking
with polynomial 0x07 and initial value 0xaa.

Source: tpms_hyundai_vdo.c
Modulation: FSK_PULSE_PCM, chip=52 us
Manchester decode, 80 bits (10 bytes)
CRC-8 poly=0x07 init=0xaa; crc8(b[0:9], 0x07, 0xaa) == b[9]
Pressure = b[6] * 1.375 kPa; Temperature = b[7] - 50 deg C
Byte 0: state; Bytes 1-4: ID; Byte 5: flags(hi4) + repeat(lo4)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _bits_to_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSHyundaiVDO(FSKPCMDecoder):
    """Hyundai TPMS (VDO)  FSK/Manchester, CRC-8."""

    name     = "Hyundai-TPMS-VDO"
    bit_rate = 1_000_000.0 / 52
    n_bits   = 200
    freq_hz  = 433.92e6

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        for offset in range(min(32, len(chips))):
            decoded = _mc_decode(chips[offset:], 88)
            if len(decoded) < 80:
                continue
            b = _bits_to_bytes(decoded[:80])
            if len(b) < 10:
                continue
            if crc8(b[:9], 0x07, 0xAA) != b[9]:
                continue

            state  = b[0]
            sid    = (b[1] << 24) | (b[2] << 16) | (b[3] << 8) | b[4]
            flags  = b[5] >> 4
            repeat = b[5] & 0x0F
            pres   = round(b[6] * 1.375, 1)
            temp   = b[7] - 50
            batt   = b[8]

            return DecodedPacket.from_fields("Hyundai-TPMS-VDO", self.freq_hz, {
                "id":            f"{sid:08x}",
                "state":         f"{state:02x}",
                "flags":         flags,
                "repeat":        repeat,
                "pressure_kPa":  pres,
                "temperature_C": temp,
                "maybe_battery": batt,
            })
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSHyundaiVDO"]
