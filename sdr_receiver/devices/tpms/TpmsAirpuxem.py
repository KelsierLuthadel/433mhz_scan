"""Airpuxem TYH11 TPMS sensor.

Airpuxem TYH11_EU6_ZQ TPMS decoder.

FSK_PULSE_PCM chip=52 µs Manchester-encoded.
Preamble (inverted): 0xaa 0xaa 0xa9.
After Manchester decode (min 84 bits):
  [0:4]   header nibble = 0x5
  [4:36]  32-bit ID
  [36:40] MSB_ONE  - bits[3:2]=pressure[9:8], [1:0]=flags
  [40:44] MSB_TWO  - bits[3:1]=position, [0]=pressure_extra
  [44:52] pressure_lsb (8 bits)
  [52:60] temperature (signed)
  [60:68] battery raw (*0.02 V)
  [68:76] CRC-8(poly=0x2f, init=0xaa) over bits[4:68] as 8 bytes

Source: tpms_airpuxem.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _pulses_to_chips, _manchester_decode, _bits_to_bytes_n, _find_pattern
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsAirpuxem(RawDecoder):
    """Airpuxem TYH11_EU6_ZQ TPMS sensor."""

    name = "Airpuxem-TYH11"
    _chip_us = 52.0
    _preamble = [1, 0, 1, 0, 1, 0, 1, 0,  # 0xaa
                 1, 0, 1, 0, 1, 0, 1, 0,  # 0xaa
                 1, 0, 1, 0, 1, 0, 0, 1]  # 0xa9

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        chips = _pulses_to_chips(pulses, self._chip_us)
        # Signal is inverted; flip all chips
        chips = [1 - c for c in chips]

        pos = _find_pattern(chips, self._preamble)
        if pos < 0:
            return None
        chips = chips[pos + len(self._preamble):]

        bits = _manchester_decode(chips)
        if bits is None or len(bits) < 84:
            return None

        # 4-bit header must be 0x5
        if bits_to_int(bits[0:4]) != 0x5:
            return None

        device_id = bits_to_int(bits[4:36])
        msb_one   = bits_to_int(bits[36:40])  # bits[3:2]=pressure[9:8], [1:0]=flags
        msb_two   = bits_to_int(bits[40:44])  # bits[3:1]=position, [0]=pressure_extra
        pres_lsb  = bits_to_int(bits[44:52])
        temp_raw  = bits_to_int(bits[52:60])
        batt_raw  = bits_to_int(bits[60:68])
        crc_rx    = bits_to_int(bits[68:76])

        data_bytes = _bits_to_bytes_n(bits[4:], 8)
        if data_bytes is None:
            return None
        if crc8(data_bytes, poly=0x2f, init=0xaa) != crc_rx:
            return None

        pressure_raw = ((msb_one >> 2) << 8) | pres_lsb
        pressure_kpa = pressure_raw + 100.0

        # temperature is signed 8-bit
        if temp_raw >= 128:
            temp_raw -= 256
        temperature_c = float(temp_raw)

        battery_v = batt_raw * 0.02
        flags     = msb_one & 0x3
        position  = (msb_two >> 1) & 0x7

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{device_id:08x}",
            "position":      position,
            "flags":         flags,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": temperature_c,
            "battery_V":     round(battery_v, 2),
            "mic":           "CRC",
        })


__all__ = ["TpmsAirpuxem"]
