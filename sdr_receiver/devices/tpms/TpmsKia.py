"""Kia Rio UB III (UB) 2011-2017 TPMS sensor and some Hyundai models too.

Copyright (C) 2022 Lasse Mikkel Reinhold, Todor Uzunov aka teou, TTiges,
2019 Andreas Spiess, 2017 Christian W. Zuckschwerdt <zany@triq.net>

Kia TPMS decoder.

Handles tire pressure monitoring system sensors from Kia Rio III models
(2011-2017) and certain Hyundai vehicles. Sensors activate around 40 km/h due to
centripetal force detection and transmit 4-6 packets twice per minute.
Packets contain 154 bits structured as a 16-bit preamble (0xed71), unknown field,
8-bit pressure (PSI * 5), 8-bit temperature (Celsius + 50), 32-bit sensor ID,
unknown bytes, and 5-bit CRC.

Source: tpms_kia.c
Modulation: FSK_PULSE_PCM (-s 1000k), chip=~50 us, Manchester-encoded
Preamble: 0xed71 (16 bits)
Payload after Manchester decode - 9 bytes (from 138 post-preamble bits):
  nibble a[3:0]  unknown1 (typically 0xf)
  b[0]           pressure raw (/ 5.0 PSI)
  b[1]           temperature raw (- 50 deg C)
  b[2:6]         ID (32-bit)
  b[6][11:0]     unknown2
  b[8][7:3]      CRC-8 poly=0x07 init=0x76 over b[0:8]
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsKia(RawDecoder):
    """Kia TPMS sensor  FSK_PULSE_PCM (-s 1000k), chip≈50 µs, Manchester-encoded.

    Preamble: 0xed71 (16 bits).
    Payload after Manchester decode  9 bytes (from 138 post-preamble bits):
      nibble a[3:0]  unknown1 (typically 0xf)
      b[0]           pressure raw (/ 5.0 PSI)
      b[1]           temperature raw (- 50 deg C)
      b[2:6]         ID (32-bit)
      b[6][11:0]     unknown2
      b[8][7:3]      CRC-8 poly=0x07 init=0x76 over b[0:8]
    """

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:  # noqa: ARG002
        return None  # FSK requires frequency-domain front-end


__all__ = ["TpmsKia"]
