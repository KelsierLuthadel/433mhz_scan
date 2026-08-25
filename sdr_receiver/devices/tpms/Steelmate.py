"""Steelmate TPMS FSK protocol.

Copyright (C) 2016 Benjamin Larsson, Copyright (C) 2016 John Jore,
Copyright (C) 2025 Bruno OCTAU (ProfBoc75)

Steelmate TPMS decoder  model TP-S15 sensors manufactured by Steelmate and R-Lake.

The protocol uses a 9-byte payload with inverted Manchester encoding and swapped
MSB/LSB ordering. Data fields include sensor synchronization, preamble, ID,
pressure measurement (in Bar at scale 32), temperature (Celsius plus 50 offset),
battery voltage, and checksum. Special alarm conditions: 0xFF triggers a fast leak
alert, while 0xFE indicates a slow leak alarm.

Source: steelmate.c
Modulation: FSK_PULSE_MANCHESTER_ZEROBIT, chip=~50 us
Valid packet lengths: 72, 73, 208, or 209 raw bits
NOTE: FSK modulation  returns None without FSK front-end.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Steelmate(RawDecoder):
    """Steelmate TPMS  FSK_PULSE_MANCHESTER_ZEROBIT, chip≈50 µs.

    Valid packet lengths: 72, 73, 208, or 209 raw bits.
    Inverted Manchester with reversed MSB/LSB -> 9 bytes:
      b[0:2]  sync
      b[2]    preamble
      b[3:5]  ID (16-bit)
      b[5]    pressure raw (* 3.125 kPa)
      b[6]    temperature raw (- 50 deg C)
      b[7]    battery (3900 - raw*10 mV); 0xFF=fast_leak, 0xFE=slow_leak
      b[8]    checksum = sum(b[2:8]) & 0xFF
    NOTE: FSK modulation  returns None without FSK front-end.
    """

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:  # noqa: ARG002
        return None  # FSK requires frequency-domain front-end


__all__ = ["Steelmate"]
