"""Microchip HCS361 KeeLoq Code Hopping Encoder based remotes.

Copyright (C) 2024 Ethan Halsall

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Microchip HCS361 KeeLoq Code Hopping Encoder based remotes.

Data Format:

66 bits transmitted, LSB first.

Extended Serial Number Disabled:

|  0-31 | Encrypted Portion
| 32-59 | Serial Number
| 60-63 | Button Status (S3, S0, S1, S2)
|  64   | Battery Low
| 65-66 | CRC

Extended Serial Number Enabled:

|  0-31 | Encrypted Portion
| 32-63 | Serial Number
|  64   | Battery Low
| 65-66 | CRC

Note that the button bits are (MSB/first sent to LSB) S3, S0, S1, S2.
Hardware buttons might map to combinations of these bits.

- Datasheet HCS361: https://ww1.microchip.com/downloads/aemDocuments/documents/MCU08/ProductDocuments/DataSheets/40146F.pdf

Known Devices:
- Manufacturer / Model
  - Leer - OUTE_ELC (FCC ID KOBLEAR1XT)
  - Marelli - (FCC ID KBRASTU15)
  - Jeep / Chrysler remote

Pulse Format / Timing:

PWM timings and code format varies based on EEPROM configuration.

Logic:
- 0 = long
- 1 = short

Timing is selected by the two flags coded into the EEPROM.

- TXWAK: Bit Format Select Or Wake-Up
  - When VPWM is enabled, this bit will enable the wake-up signal.
- BSEL: Baud Rate Select
  - When disabled, baud rate is 833 bits / second.
  - When enabled, baud rate is 1667 bits / second.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from .._helpers import _bits_to_bytes_lsb
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HCS361(OOKPWMDecoder):
    """Microchip HCS361 KeeLoq rolling-code remote (OOK_PULSE_PWM).

    400/800 µs, 66 bits + 2-bit CRC LSB-first.
    Same 66-bit layout as HCS200; 2-bit CRC appended.
    """

    name      = "Microchip-HCS361"
    short_us  = 400.0
    long_us   = 800.0
    reset_us  = 7200.0
    n_bits    = 69   # 66 data + 2 CRC + 1 margin
    tolerance = 0.45

    @staticmethod
    def _crc2(bits: list[int]) -> int:
        crc1 = crc0 = 0
        for b in bits[:65]:
            crc1, crc0 = crc0 ^ b, crc0 ^ b ^ crc1
        return (crc1 << 1) | crc0

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 67:
            return None
        crc_calc = self._crc2(bits)
        # bits[65]=CRC0, bits[66]=CRC1 → stored value = (CRC1<<1)|CRC0
        crc_recv = (bits[66] << 1) | bits[65]
        if crc_calc != crc_recv:
            return None
        raw = _bits_to_bytes_lsb(bits[:64])
        if all(b == 0xFF for b in raw):
            return None
        enc    = (raw[0] << 24) | (raw[1] << 16) | (raw[2] << 8) | raw[3]
        serial = raw[4] | (raw[5] << 8) | (raw[6] << 16) | ((raw[7] & 0x0F) << 24)
        btn_ny = (raw[7] >> 4) & 0xF
        s3 = (btn_ny >> 3) & 1; s0 = (btn_ny >> 2) & 1
        s1 = (btn_ny >> 1) & 1; s2 = (btn_ny >> 0) & 1
        button     = (s0 << 3) | (s1 << 2) | (s2 << 1) | s3
        battery_ok = not bool(bits[64])
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         f"{serial:07X}",
            "button":     button,
            "battery_ok": int(battery_ok),
            "encrypted":  f"{enc:08X}",
            "mic":        "CRC",
        })


__all__ = ["HCS361"]
