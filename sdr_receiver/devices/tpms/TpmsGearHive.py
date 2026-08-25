"""Gear Hive unbranded aftermarket TPMS sensor.

Gear Hive TPMS decoder.

OOK_PULSE_MANCHESTER_ZEROBIT short=120 µs long=224 µs.
Sync word: 0x2594 (16 bits).
9 bytes after sync, differential XOR decoded (seed 0x94):
  p[0] = b[0] ^ 0x94;  p[n] = b[n] ^ b[n-1]
  B0-B1 : counter(12b) | class(4b)
  B2-B4 : 24-bit sensor ID
  B5    : pressure raw
  B6-B7 : temperature encoding (valid if (B6&0x3c)==0x20 and (B7&0x3f)==0x35)
  B8    : unknown
pressure = ((raw - base + 256) & 0xff) * 6.25 kPa
temperature = temp_bits + 21.0
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _bits_to_bytes_n
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsGearHive(ManchesterDecoder):
    """Gear Hive unbranded aftermarket TPMS sensor."""

    name     = "GearHive-TPMS"
    chip_us  = 120.0
    reset_us = 800.0
    n_bits   = 88 + 16  # sync + 9 bytes

    # Pressure base by sensor class
    _BASE = {0: 0, 1: 20, 2: 40, 3: 60}

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Find sync pattern 0x2594
        sync = [0, 0, 1, 0, 0, 1, 0, 1,  # 0x25
                1, 0, 0, 1, 0, 1, 0, 0]  # 0x94
        pos = -1
        for i in range(len(bits) - len(sync) - 72 + 1):
            if bits[i: i + len(sync)] == sync:
                pos = i + len(sync)
                break
        if pos < 0 or pos + 72 > len(bits):
            return None

        raw = _bits_to_bytes_n(bits[pos:], 9)
        if raw is None:
            return None

        # Differential XOR decode seeded with 0x94
        p = bytearray(9)
        p[0] = raw[0] ^ 0x94
        for i in range(1, 9):
            p[i] = raw[i] ^ raw[i - 1]

        # Sanity checks on fixed bit fields
        if (p[6] & 0x3c) != 0x20:
            return None
        if (p[7] & 0x3f) != 0x35:
            return None

        counter     = ((p[0] << 4) | (p[1] >> 4)) & 0xFFF
        sensor_cls  = p[1] & 0x0F
        sensor_id   = (p[2] << 16) | (p[3] << 8) | p[4]
        pres_raw    = p[5]
        temp_bits   = ((p[6] >> 6) & 0x3) | ((p[7] >> 4) & 0xC)  # 4 bits

        base        = self._BASE.get(sensor_cls, 0)
        pressure_kpa = ((pres_raw - base + 256) & 0xFF) * 6.25
        temperature_c = temp_bits + 21.0

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:06x}",
            "class":         sensor_cls,
            "counter":       counter,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "mic":           "CHECKSUM",
        })


__all__ = ["TpmsGearHive"]
