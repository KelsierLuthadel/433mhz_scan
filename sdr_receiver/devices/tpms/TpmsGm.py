"""General Motors Aftermarket TPMS.

Copyright (C) 2025 Eric Blevins

GM aftermarket TPMS decoder.

The decoder processes 130-bit transmissions from GM aftermarket tire pressure
monitoring sensors. The data structure includes a preamble, flags, device type,
unique identifier, pressure, temperature, and checksum. The implementation
validates the preamble pattern, computes modulo-256 checksums, and extracts sensor
readings. Learn mode activates during pressure drops or tool-assisted
initialization, transitioning to operational mode after pressurization. Status
indicators include battery condition and operational state.

Source: tpms_gm.c
Modulation: OOK_PULSE_MANCHESTER_ZEROBIT, chip=~120 us
130 decoded bits (16+ bytes)
b[0:6]   preamble (must be all 0x00)
b[6:8]   flags (16-bit); bit5=battery_low; bits0,1,8 all 0 -> learn_mode
b[8:13]  sensor ID (40-bit)
b[13]    pressure raw (* 2.75 kPa)
b[14]    temperature raw (- 60 deg C)
b[15]    checksum = sum(b[6:15]) & 0xFF
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _bits_to_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsGm(ManchesterDecoder):
    """GM aftermarket TPMS  OOK_PULSE_MANCHESTER_ZEROBIT, chip≈120 µs.

    130 decoded bits (16+ bytes).  Layout:
      b[0:6]   preamble (must be all 0x00)
      b[6:8]   flags (16-bit); bit5=battery_low; bits0,1,8 all 0 -> learn_mode
      b[8:13]  sensor ID (40-bit)
      b[13]    pressure raw (* 2.75 kPa)
      b[14]    temperature raw (- 60 deg C)
      b[15]    checksum = sum(b[6:15]) & 0xFF
    """

    name     = "GM-TPMS"
    chip_us  = 120.0
    reset_us = 15_600.0
    n_bits   = 130

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 128:
            return None
        b = _bits_to_bytes(bits[:128])
        if len(b) < 16:
            return None
        # Preamble: bytes 0-5 all zero
        if any(b[i] != 0 for i in range(6)):
            return None
        # Sanity: payload not all zero
        if all(b[i] == 0 for i in range(6, 15)):
            return None
        flags      = (b[6] << 8) | b[7]
        sensor_id  = bits_to_int(bits[64:104])   # bytes 8-12 = 40 bits
        csum       = b[15]
        if (sum(b[6:15]) & 0xFF) != csum:
            return None
        pressure_kpa = b[13] * 2.75
        temp_c       = b[14] - 60
        battery_ok   = not bool(flags & 0x0020)  # bit 5 of low byte
        learn_mode   = (flags & 0x0103) == 0     # bits 0, 1, 8 all zero
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           format(sensor_id, "010x"),
            "flags":        format(flags, "04x"),
            "pressure_kPa": round(pressure_kpa, 2),
            "temperature_C": temp_c,
            "battery_ok":   battery_ok,
            "learn_mode":   learn_mode,
        })


__all__ = ["TpmsGm"]
