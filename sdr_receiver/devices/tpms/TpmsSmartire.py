"""SmarTire TPMS sensor.

Copyright (C) 2024 Bruno OCTAU (ProfBoc75)

SmarTire TPMS decoder (Aston Martin/Vantage DB9).

The decoder handles SmarTire Vantage and Aston Martin DB9 tire pressure monitoring
system sensors from 2005-2011. It processes 10 OOK PCM and Differential Manchester-
coded messages containing pressure and temperature data, repeated five times. The
six-byte message format includes sensor identification, pressure values (offset 40,
scaled by 2.5), temperature readings, and a CRC-7 checksum for verification.

Source: tpms_smartire.c
Modulation: OOK_PULSE_PCM, differential Manchester
chip=~167 us, preamble 0x32B4 (16 bits)
Payload after diff-Manchester decode - 6 bytes:
  b[0]         value: pressure * 2.5 - 40 PSI or temperature - 40 deg C
  msg_type     = (b[1] >> 6) & 0x3  (0=pressure, 1=temperature)
  id           = 22-bit: (b[1]&0x3F)<<16 | b[2]<<8 | b[3]
  fast_inflate = (b[4] >> 7) & 1
  flags        = b[4] & 0x7F
  crc7         = b[5] & 0x7F  (poly=0x45, init=0x6f over b[0:5])
NOTE: Differential Manchester above OOK_PULSE_PCM requires specialised
chip-pair processing not yet in the standard OOK pipeline.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsSmartire(RawDecoder):
    """SmarTire TPMS (Aston Martin/Vantage DB9)  OOK_PULSE_PCM, differential Manchester.

    chip≈167 µs, preamble 0x32B4 (16 bits).
    Payload after diff-Manchester decode  6 bytes:
      b[0]         value: pressure * 2.5 - 40 PSI or temperature - 40 deg C
      msg_type     = (b[1] >> 6) & 0x3  (0=pressure, 1=temperature)
      id           = 22-bit: (b[1]&0x3F)<<16 | b[2]<<8 | b[3]
      fast_inflate = (b[4] >> 7) & 1
      flags        = b[4] & 0x7F
      crc7         = b[5] & 0x7F  (poly=0x45, init=0x6f over b[0:5])
    NOTE: Differential Manchester above OOK_PULSE_PCM requires specialised
    chip-pair processing not yet in the standard OOK pipeline.
    """

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:  # noqa: ARG002
        return None  # Diff-Manchester + CRC-7 front-end not yet integrated


__all__ = ["TpmsSmartire"]
