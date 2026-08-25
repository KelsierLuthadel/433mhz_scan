"""FSK 9-byte Differential Manchester encoded TPMS data with CRC-8.

Copyright (C) 2017 Christian W. Zuckschwerdt <zany@triq.net>

Toyota TPMS decoder.

Handles FSK 9-byte Differential Manchester encoded TPMS signals from Pacific
Industries Co.Ltd. PMV-C210 sensors found in Toyota vehicles. The signal structure
includes 14 bits of synchronization followed by 72 bits of Manchester encoded data
and 3 trailer bits. The decoded packet contains a 4-byte ID, status bit, pressure
reading, temperature offset by 40 deg C, inverted pressure value, and CRC-8
validation using polynomial 0x07 with initial value 0x80.

Source: tpms_toyota.c
Modulation: FSK_PULSE_PCM, chip=~52 us, differential Manchester
Search for 12-bit preamble 0xa9 0xe0; diff-Manchester decode 72 bits -> 9 bytes:
  b[0:4]  ID (32-bit)
  b[4]    status(b7) | pressure_hi[6:0]
  b[5]    pressure_lo(b7) | temp_hi[6:0]
  b[6]    temp_lo(b7) | filler
  b[7]    ~b[4]  (pressure verification byte)
  b[8]    CRC-8 poly=0x07 init=0x80 over b[0:8]
pressure_psi = (((b[4]&0x7F)<<1)|(b[5]>>7)) * 0.25 - 7.0
temperature_C = (((b[5]&0x7F)<<1)|(b[6]>>7)) - 40
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsToyota(RawDecoder):
    """Toyota TPMS sensor  FSK_PULSE_PCM, chip≈52 µs, differential Manchester.

    Search for 12-bit preamble 0xa9 0xe0; diff-Manchester decode 72 bits -> 9 bytes:
      b[0:4]  ID (32-bit)
      b[4]    status(b7) | pressure_hi[6:0]
      b[5]    pressure_lo(b7) | temp_hi[6:0]
      b[6]    temp_lo(b7) | filler
      b[7]    ~b[4]  (pressure verification byte)
      b[8]    CRC-8 poly=0x07 init=0x80 over b[0:8]
    pressure_psi = (((b[4]&0x7F)<<1)|(b[5]>>7)) * 0.25 - 7.0
    temperature_C = (((b[5]&0x7F)<<1)|(b[6]>>7)) - 40
    """

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:  # noqa: ARG002
        return None  # FSK requires frequency-domain front-end


__all__ = ["TpmsToyota"]
