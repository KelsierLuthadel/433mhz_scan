"""PMV-107J (Toyota) TPMS sensor.

PMV-107J TPMS decoder.

FSK_PULSE_PCM chip=100 µs Differential Manchester encoded.
6-bit preamble 0xf8 (111110), then Differential Manchester -> 9 bytes.
Layout (after realignment by 2-bit shift):
  b[0]<<26 | b[1]<<18 | b[2]<<10 | b[3]<<2 | b[4]>>6  -> 28-bit ID
  b[4] & 0x3f  -> status
    bit5: battery_low
    bits[4:3]: counter
    bit1: rapid_change
    bit0: failed
  b[5] = pressure raw (must equal ~b[6])
  b[6] = ~pressure (inverted check)
  b[7] = temperature raw
  b[8] = CRC-8(poly=0x13, init=0x00) over b[0:8]
pressure_kPa = (b[5] - 40) * 2.48
temperature_C = b[7] - 40

Source: tpms_pmv107j.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _pulses_to_chips, _diff_manchester_decode, _bits_to_bytes_n, _find_pattern
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsPmv107j(RawDecoder):
    """PMV-107J (Toyota) TPMS sensor."""

    name    = "PMV-107J"
    _chip_us = 100.0
    # 6-bit preamble: 0xf8 = 11111000, take first 6 bits = 111110
    _preamble = [1, 1, 1, 1, 1, 0]

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        chips = _pulses_to_chips(pulses, self._chip_us)

        pos = _find_pattern(chips, self._preamble)
        if pos < 0:
            return None
        remaining = chips[pos + len(self._preamble):]

        bits = _diff_manchester_decode(remaining)
        if bits is None or len(bits) < 67:
            return None

        # Realign: shift by 2 bits into b[0] header, then extract 8 bytes
        # b[0] = first 2 bits (from preamble exit), shifted right -> 0..3
        # The C code does: b[0] = packet_bits.bb[0][0] >> 6 (top 2 bits -> lower 2)
        # then extract 64 bits starting at bit offset 2
        # Simplified: treat bits[0:2] as b[0] high bits, bits[2:66] as b[1..8]
        b0_hi = bits_to_int(bits[0:2])
        rest  = _bits_to_bytes_n(bits[2:], 8)
        if rest is None:
            return None
        b = bytearray(9)
        b[0] = b0_hi
        b[1:9] = rest

        crc_rx = b[8]
        if crc8(bytes(b[:8]), poly=0x13, init=0x00) != crc_rx:
            return None

        # Pressure cross-check
        if b[5] != (b[6] ^ 0xFF):
            return None

        sensor_id    = ((b[0] << 26) | (b[1] << 18) | (b[2] << 10) |
                        (b[3] << 2)  | (b[4] >> 6)) & 0x0FFFFFFF
        status       = b[4] & 0x3F
        battery_low  = bool((b[4] >> 5) & 1)
        counter      = (b[4] >> 3) & 0x3
        rapid_change = bool((b[4] >> 1) & 1)
        failed       = bool(b[4] & 1)
        pressure_kpa = (b[5] - 40.0) * 2.48
        temperature_c = b[7] - 40.0

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{sensor_id:07x}",
            "status":        status,
            "battery_ok":    not battery_low,
            "counter":       counter,
            "rapid_change":  rapid_change,
            "failed":        "FAIL" if failed else "OK",
            "pressure_kPa":  round(pressure_kpa, 1),
            "temperature_C": round(temperature_c, 1),
            "mic":           "CRC",
        })


__all__ = ["TpmsPmv107j"]
