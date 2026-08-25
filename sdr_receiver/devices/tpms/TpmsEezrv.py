"""EezTire E618 TPMS sensor.

EezTire E618 TPMS decoder.

OOK_PULSE_MANCHESTER_ZEROBIT chip=50 µs n_bits=80 (payload after preamble).
Frame (from Manchester-decoded stream):
  [0:16]   preamble 0xFFFF (skip)
  [16:24]  checksum byte
  [24:48]  24-bit ID (little-endian byte order)
  [48:56]  pressure raw
  [56:64]  temperature raw (-50 deg C)
  [64:72]  flags1
  [72:80]  flags2
Pressure: ((flags2 & 0x01) << 8 | pressure_raw) * 2.5 kPa
Checksum: sum all 7 payload bytes; if >0xff OR in bit7, check accordingly.

Source: tpms_eezrv.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsEezrv(ManchesterDecoder):
    """EezTire E618 TPMS sensor."""

    name     = "EezTire-E618"
    chip_us  = 50.0
    reset_us = 120.0
    n_bits   = 80  # 16 preamble + 8 cksum + 24 id + 8 pres + 8 temp + 16 flags

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 80:
            return None

        # Locate preamble 0xFF 0xFF = 16 ones
        start = -1
        for i in range(len(bits) - 79):
            if all(bits[i + j] == 1 for j in range(16)):
                start = i + 16
                break
        if start < 0 or start + 64 > len(bits):
            return None

        cksum_byte  = bits_to_int(bits[start:     start + 8])
        id_b0       = bits_to_int(bits[start + 8: start + 16])
        id_b1       = bits_to_int(bits[start + 16:start + 24])
        id_b2       = bits_to_int(bits[start + 24:start + 32])
        pressure_r  = bits_to_int(bits[start + 32:start + 40])
        temp_raw    = bits_to_int(bits[start + 40:start + 48])
        flags1      = bits_to_int(bits[start + 48:start + 56])
        flags2      = bits_to_int(bits[start + 56:start + 64])

        payload = bytes([id_b0, id_b1, id_b2, pressure_r, temp_raw, flags1, flags2])
        chk_calc = sum(payload) & 0xFF
        if (sum(payload) > 0xFF):
            chk_calc |= 0x80
        if chk_calc != cksum_byte:
            return None

        sensor_id    = id_b0 | (id_b1 << 8) | (id_b2 << 16)  # little-endian
        pressure_kpa = (((flags2 & 0x01) << 8) | pressure_r) * 2.5
        temperature_c = temp_raw - 50.0
        battery_low  = bool((flags1 >> 7) & 1)
        fast_deflate = bool((flags1 >> 4) & 1)
        inflating    = bool((flags1 >> 5) & 1)

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:06x}",
            "battery_ok":    not battery_low,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "fast_deflate":  fast_deflate,
            "inflating":     inflating,
            "mic":           "CHECKSUM",
        })


__all__ = ["TpmsEezrv"]
