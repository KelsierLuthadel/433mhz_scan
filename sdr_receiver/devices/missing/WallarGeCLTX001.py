"""WallarGe CLTX001 Outdoor Temperature Sensor.

Copyright (C) 2026 Dennis Kehrig

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

WallarGe CLTX001 Outdoor Temperature Sensor.

FCC ID: 2AYIQ-TX100 (https://fcc.report/FCC-ID/2AYIQ-TX100)

Can be purchased individually or bundled with WallarGe clocks like the
CL6007 and CL7001.

Payload encoding: 56 bits / 7 bytes

1. IIIIIIII - Bits 1 to 8 of a uint16_t sensor ID
2. IIIIIIII - Bits 9 to 16 of a uint16_t sensor ID
3. 00000000 - Always zero, unknown purpose
4. BMCCTTTT - Battery status (0=okay, 1=low), test mode, 2-bit channel ID,
              bits 1 to 4 of an int12_t temperature reading
5. TTTTTTTT - Bits 5 to 12 of an int12_t temperature reading
6. PPPPP000 - Parity data
7. SSSSSSSS - Checksum, sum of bytes 1-5 (indexes 0-4) modulo 256

Temperature: 12 bit signed integer (two's complement) representing 0.1 degC increments.
Range: -204.8 to 204.7 degC.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class WallarGeCLTX001(OOKPWMDecoder):
    """WallarGe CLTX001 outdoor temperature sensor.
    OOK_PULSE_PWM, 56 bits (7 bytes).
    Byte layout: ID(2) Reserved(1) Ctrl(1) TempLo(1) Parity(1) CRC(1).
    Checksum: sum of bytes 0-4 mod 256 == byte 6.
    """
    name     = "WallarGe-CLTX001"
    short_us = 250.0
    long_us  = 500.0
    reset_us = 1250.0
    n_bits   = 56

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        data = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 56, 8))
        if (sum(data[:5]) & 0xFF) != data[6]:
            return None
        device_id = (data[0] << 8) | data[1]
        # data[2] = reserved (0x00)
        ctrl      = data[3]
        battery   = (ctrl >> 7) & 1
        channel   = ((ctrl >> 4) & 0x3) + 1
        temp_hi4  = ctrl & 0xF           # high 4 bits of 12-bit temp
        temp_lo8  = data[4]
        temp_raw  = (temp_hi4 << 8) | temp_lo8   # 12-bit value
        if temp_raw & 0x800:
            temp_c = (temp_raw - 0x1000) / 10.0
        else:
            temp_c = temp_raw / 10.0
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    1 - battery,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["WallarGeCLTX001"]
