"""Mercedes Benz Sprinter TPMS data.

Copyright (C) 2026 Bruno OCTAU (ProfBoc75)

Mercedes Benz Sprinter TPMS decoder.

The decoder processes 2025 Mercedes Benz Sprinter 4500 TPMS sensor signals using
FSK modulation with 25-microsecond pulse width. It searches for a 12-bit preamble
(0x002 or 0xff2), then extracts 10 bytes of data containing: state/family byte,
32-bit ID, pressure (PSI scaled by 2.75), temperature (deg C with -51 offset),
counter, status flags, and CRC-8 checksum with polynomial 0x2f and initialization
value 0xaa.

Source: tpms_mercedes_benz.c
Modulation: FSK_PULSE_MANCHESTER_ZEROBIT, chip=25 us
12-bit preamble 0x002 then 80 bits (10 bytes)
CRC-8 poly=0x2f init=0xaa over 10 bytes (result must be 0)
Pressure = byte / 2.75 PSI; Temperature = byte - 51 deg C
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _bits_to_bytes, _find_pattern, _int_to_bits
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSMercedesBenz(FSKManchesterDecoder):
    """Mercedes-Benz Sprinter TPMS  FSK/Manchester, CRC-8."""

    name     = "Mercedes-Benz-TPMS"
    bit_rate = 1_000_000.0 / 25   # chip rate; Manchester halves data rate
    n_bits   = 100                 # decoded Manchester bits needed (min)
    freq_hz  = 433.92e6

    # Preamble is 12-bit pattern 0x002 in the Manchester-decoded bit stream
    _PREAMBLE = _int_to_bits(0x002, 12)

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        pos = _find_pattern(bits, self._PREAMBLE)
        if pos < 0:
            return None
        pos += 12

        if pos + 80 > len(bits):
            return None
        b = _bits_to_bytes(bits[pos : pos + 80])
        if len(b) < 10:
            return None
        if crc8(b, 0x2F, 0xAA) != 0:
            return None

        state = b[0]
        if state not in (0x83, 0xA3):
            return None
        sid     = (b[1] << 24) | (b[2] << 16) | (b[3] << 8) | b[4]
        pres    = round(b[5] / 2.75, 1)
        temp    = b[6] - 51
        counter = b[7] & 0x1F
        flags1  = b[7] >> 5
        flags2  = b[8]

        return DecodedPacket.from_fields("Mercedes-Benz-TPMS", freq_hz, {
            "id":            f"{sid:08x}",
            "state":         "moving" if state == 0xA3 else "stationary",
            "pressure_PSI":  pres,
            "temperature_C": temp,
            "counter":       counter,
            "flags1":        flags1,
            "flags2":        flags2,
        })


__all__ = ["TPMSMercedesBenz"]
