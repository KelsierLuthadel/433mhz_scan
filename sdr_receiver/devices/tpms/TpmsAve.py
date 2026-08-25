"""AVE TPMS sensor.

AVE TPMS decoder.

FSK_PULSE_PCM chip=100 µs Differential Manchester encoded.
Preamble raw pattern: 0xcc 0xcc 0xcc 0xcd (32 bits).
After Differential Manchester decode -> 11 bytes:
  B0-B3  : 32-bit sensor ID
  B4     : pressure raw
  B5     : temperature raw (-50 deg C)
  B6     : {mode[1:0], battery[2:0], flags[2:0]}
  B7     : CRC-8(poly=0x31, init=0xff) over B0-B7
Pressure modes 0/1: kPa = raw*2.352 - {47.0, 0.0}
Pressure modes 2/3: kPa = raw*5.491 - {18.2, 0.0}

Source: tpms_ave.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _pulses_to_chips, _diff_manchester_decode, _bits_to_bytes_n, _find_pattern
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsAve(RawDecoder):
    """AVE TPMS sensor."""

    name = "AVE-TPMS"
    _chip_us = 100.0
    # Preamble bit pattern for 0xcc,0xcc,0xcc,0xcd
    _preamble_bytes = bytes([0xcc, 0xcc, 0xcc, 0xcd])

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        chips = _pulses_to_chips(pulses, self._chip_us)
        if len(chips) < 32 + 22 * 2:
            return None

        # Search for the 32-bit preamble as raw chips (no Manchester)
        preamble_chips: list[int] = []
        for byte in self._preamble_bytes:
            for bit_idx in range(7, -1, -1):
                preamble_chips.append((byte >> bit_idx) & 1)

        pos = _find_pattern(chips, preamble_chips)
        if pos < 0:
            return None
        # Differential Manchester starts right after preamble
        remaining = chips[pos + len(preamble_chips):]
        bits = _diff_manchester_decode(remaining)
        if bits is None or len(bits) < 88:
            return None

        data = _bits_to_bytes_n(bits, 11)
        if data is None:
            return None

        # CRC over first 8 bytes, result in byte 7
        if crc8(data[:7], poly=0x31, init=0xff) != data[7]:
            return None

        sensor_id   = (data[0] << 24 | data[1] << 16 | data[2] << 8 | data[3])
        pressure_raw = data[4]
        temperature_c = data[5] - 50.0
        mode        = (data[6] >> 6) & 0x3
        battery_ok  = bool((data[6] >> 3) & 0x1)

        _offsets   = [47.0, 0.0, 18.2, 0.0]
        _scales    = [2.352, 2.352, 5.491, 5.491]
        pressure_kpa = pressure_raw * _scales[mode] - _offsets[mode]

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:08x}",
            "mode":          mode,
            "battery_ok":    battery_ok,
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "mic":           "CRC",
        })


__all__ = ["TpmsAve"]
