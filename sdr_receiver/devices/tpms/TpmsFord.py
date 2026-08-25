"""FSK 8 byte Manchester encoded TPMS with simple checksum.

Copyright (C) 2017 Christian W. Zuckschwerdt

Ford TPMS decoder.

Handles FSK-modulated tire pressure monitoring system signals observed on Ford
vehicles including Fiesta, Focus, Kuga, Escape, and Transit models. The 8-byte
Manchester-encoded packets transmit sensor ID, pressure (in PSI units),
temperature data, operational flags indicating movement or learning mode, and a
checksum. Transmissions typically occur four times per event, with sensors
operating in three modes: moving, at-rest, and learn. Signals operate on 315 MHz
(US) and 433.92 MHz frequencies, likely from Continental VDO sensors.

Source: tpms_ford.c
Modulation: FSK_PULSE_PCM, chip=~52 us, Manchester-encoded
Preamble: 0xaa 0xa9 (16 bits)
Payload after Manchester decode - 8 bytes:
  b[0:4]  ID (32-bit)
  b[4]    pressure low byte
  b[5]    temperature; (b[5]&0x7F)-56 deg C; invalid if b[5]&0x80
  b[6]    flags: 0x40=moving, 0x20=pressure_bit9, 0x08=learn, 0x04=at-rest
  b[7]    checksum = sum(b[0:7]) & 0xFF
pressure_psi = ((b[6]&0x20)<<3 | b[4]) * 0.25
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsFord(RawDecoder):
    """Ford TPMS sensor  FSK_PULSE_PCM, chip≈52 µs, Manchester-encoded.

    Preamble: 0xaa 0xa9 (16 bits).
    Payload after Manchester decode  8 bytes:
      b[0:4]  ID (32-bit)
      b[4]    pressure low byte
      b[5]    temperature; (b[5]&0x7F)-56 °C; invalid if b[5]&0x80
      b[6]    flags: 0x40=moving, 0x20=pressure_bit9, 0x08=learn, 0x04=at-rest
      b[7]    checksum = sum(b[0:7]) & 0xFF
    pressure_psi = ((b[6]&0x20)<<3 | b[4]) * 0.25
    """

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:  # noqa: ARG002
        return None  # FSK requires frequency-domain front-end


__all__ = ["TpmsFord"]
