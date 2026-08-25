"""TRW TPMS Sensor decoder.

Copyright (C) 2025 Bruno OCTAU @ProfBoc75

TRW TPMS decoder for Chrysler vehicles (2014-2022).

The decoder handles TRW tire pressure monitoring system signals (FCC-ID: GQ4-70T)
transmitted via OOK and FSK modulation. It processes 88-bit messages containing
sensor identification, pressure readings (scaled by 2.5 PSI), temperature data
(offset -50 deg C), motion status, and CRC-8/SMBUS integrity checking. The
implementation supports both OEM and clone OEM models.

Source: tpms_trw.c
OOK variant: OOK_PULSE_MANCHESTER_ZEROBIT, chip=52 us, reset=150 us
11-byte message after preamble 0x0001
Byte 0: mode (0x5c stationary, 0x5d rolling, 0x5e fast)
Bytes 1-4: sensor ID (32-bit)
Byte 5: flags (hi 4) + sequence (lo 4)
Byte 6: pressure (raw * 0.4 PSI -> kPa)
Byte 7: temperature (raw - 50 deg C)
Byte 8: motion status
Byte 9: CRC-8/SMBUS poly=0x07 init=0x00 over bytes 0-8
Byte 10: model/OEM identifier
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _bits_to_bytes, _find_pattern, _int_to_bits
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSTRW(ManchesterDecoder):
    """TRW TPMS (OOK variant)  OOK Manchester, CRC-8."""

    name     = "TRW-TPMS"
    chip_us  = 52.0
    reset_us = 150.0
    n_bits   = 104   # preamble 16 + message 88
    inverted = False

    _PREAMBLE = _int_to_bits(0x0001, 16)
    _MODES    = {0x5C: "stationary", 0x5D: "rolling", 0x5E: "fast"}

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        pos = _find_pattern(bits, self._PREAMBLE)
        if pos < 0:
            return None
        pos += 16
        if pos + 88 > len(bits):
            return None
        b = _bits_to_bytes(bits[pos : pos + 88])
        if len(b) < 11:
            return None
        if b[0] not in self._MODES:
            return None
        if crc8(b[:9], 0x07, 0x00) != b[9]:
            return None

        sid    = (b[1] << 24) | (b[2] << 16) | (b[3] << 8) | b[4]
        flags  = b[5] >> 4
        seq    = b[5] & 0x0F
        pres   = round(b[6] * 0.4 * 6.895, 1)   # PSI -> kPa
        temp   = b[7] - 50
        motion = b[8]

        return DecodedPacket.from_fields("TRW-TPMS", freq_hz, {
            "id":            f"{sid:08x}",
            "mode":          self._MODES[b[0]],
            "flags":         flags,
            "sequence":      seq,
            "pressure_kPa":  pres,
            "temperature_C": temp,
            "motion":        motion,
        })


__all__ = ["TPMSTRW"]
