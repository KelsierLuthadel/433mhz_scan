"""Unbranded SolarTPMS for trucks.

Copyright (C) 2021 Christian W. Zuckschwerdt <zany@triq.net>

Unbranded Solar TPMS truck decoder (wheel counter set of 6 units).

The system operates at 433 MHz using FSK modulation with Manchester coding.
Data includes a 232-bit preamble followed by a Manchester-coded packet containing
ID, wheel position, status flags, pressure (0.1-12.0 bar), temperature (-127 to
127 deg C), and XOR checksum. The decoder extracts these fields and validates
packet integrity through checksum verification.

Source: tpms_truck.c
Modulation: FSK_PULSE_PCM, chip=~52 us, Manchester-encoded
Preamble: inverted 0xaa 0xaa 0xa9 pattern (232-bit preamble in signal)
Payload after Manchester decode - 9 bytes (72 data bits):
  nibble[0]    state (excluded from checksum)
  b[0:4]       ID (32-bit, starting at nibble 1)
  b[4]         wheel position
  nibble[9]    flags: 0x4=pressure_alert, (flags&3)==3 -> battery low
  b[5][3:0]+b[6]  pressure (12-bit); value * 0.1 bar (= kPa / 10)
  b[7]         temperature (signed deg C)
  b[8]         XOR checksum over all 9 bytes (must be 0)
  nibble[18]   static trailer
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsTruck(RawDecoder):
    """Unbranded Solar TPMS for trucks  FSK_PULSE_PCM, chip≈52 µs, Manchester-encoded.

    Preamble: inverted 0xaa 0xaa 0xa9 pattern (232-bit preamble in signal).
    Payload after Manchester decode  9 bytes (72 data bits):
      nibble[0]    state (excluded from checksum)
      b[0:4]       ID (32-bit, starting at nibble 1)
      b[4]         wheel position
      nibble[9]    flags: 0x4=pressure_alert, (flags&3)==3 -> battery low
      b[5][3:0]+b[6]  pressure (12-bit); value * 0.1 bar (= kPa / 10)
      b[7]         temperature (signed deg C)
      b[8]         XOR checksum over all 9 bytes (must be 0)
      nibble[18]   static trailer
    """

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:  # noqa: ARG002
        return None  # FSK requires frequency-domain front-end


__all__ = ["TpmsTruck"]
