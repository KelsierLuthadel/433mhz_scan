"""Jeep TPMS sensor.

Jeep TPMS decoder.

FSK_PULSE_PCM chip=52 µs Manchester-encoded.
Preamble (inverted): 0xaa 0xaa 0xa9 -> Manchester decode -> 10 bytes:
  B0:    state (not checksummed)
  B1-B4: 32-bit sensor ID
  B5:    flags[7:4] | repeat_counter[3:0]
  B6:    pressure raw (* 2.728 kPa)
  B7:    temperature raw (-50 deg C)
  B8:    battery indicator
  B9:    XOR checksum (XOR of B1..B9 == 0)

Source: tpms_jeep.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _pulses_to_chips, _manchester_decode, _bits_to_bytes_n, _find_pattern
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsJeep(RawDecoder):
    """Jeep TPMS sensor."""

    name    = "Jeep-TPMS"
    _chip_us = 52.0
    _preamble = [1, 0, 1, 0, 1, 0, 1, 0,  # 0xaa
                 1, 0, 1, 0, 1, 0, 1, 0,  # 0xaa
                 1, 0, 1, 0, 1, 0, 0, 1]  # 0xa9

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        chips = _pulses_to_chips(pulses, self._chip_us)
        chips = [1 - c for c in chips]  # invert

        pos = _find_pattern(chips, self._preamble)
        if pos < 0:
            return None
        remaining = chips[pos + len(self._preamble):]

        bits = _manchester_decode(remaining)
        if bits is None or len(bits) < 80:
            return None

        b = _bits_to_bytes_n(bits, 10)
        if b is None:
            return None

        # XOR checksum: XOR of b[1:10] must be 0
        xor_val = 0
        for byte in b[1:10]:
            xor_val ^= byte
        if xor_val != 0:
            return None

        sensor_id    = (b[1] << 24) | (b[2] << 16) | (b[3] << 8) | b[4]
        flags        = (b[5] >> 4) & 0xF
        repeat       = b[5] & 0xF
        pressure_kpa  = b[6] * 2.728
        temperature_c  = b[7] - 50.0
        battery_raw  = b[8]

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:08x}",
            "state":         b[0],
            "flags":         flags,
            "repeat":        repeat,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "battery":       battery_raw,
            "mic":           "CHECKSUM",
        })


__all__ = ["TpmsJeep"]
