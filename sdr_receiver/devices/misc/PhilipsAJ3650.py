"""Philips AJ3650 outdoor temperature sensor.

Copyright (C) 2017 Chris Coffey <kpuc@sdf.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Philips outdoor temperature sensor -- used with various Philips clock
radios (tested on AJ3650).

Not tested, but these should also work: AJ260 ... maybe others?

A complete message is 112 bits:
- 4-bit initial preamble, always 0
- 4-bit packet separator, always 0, followed by 32-bit data packet.
- Packets are repeated 3 times for 108 bits total.

32-bit data packet format:

    0001cccc tttttttt tt000000 0b0?ssss

- c: channel: 0=channel 2, 2=channel 1, 4=channel 3 (4 bits)
- t: temperature in Celsius: subtract 500 and divide by 10 (10 bits)
- b: battery status: 0 = OK, 1 = LOW (1 bit)
- ?: unknown: always 1 in every packet I've seen (1 bit)
- s: CRC: non-standard CRC-4, poly 0x9, init 0x1

Pulse width:
- Short: 2000 us = 0
- Long: 6000 us = 1
Gap width:
- Short: 6000 us
- Long: 2000 us
Gap width between packets: 29000 us
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class PhilipsAJ3650(OOKPWMDecoder):
    """Philips outdoor temperature sensor (AJ3650)."""
    name     = "Philips-AJ3650"
    short_us = 2000.0
    long_us  = 6000.0
    reset_us = 30000.0
    n_bits   = 112

    _CH_MAP = {0: 2, 2: 1, 4: 3}

    @staticmethod
    def _crc4(data_bits: list) -> int:
        """CRC-4 poly=0x9, init=0x1 over 28 bits."""
        crc = 0x1
        for bit in data_bits[:28]:
            if ((crc >> 3) ^ bit) & 1:
                crc = ((crc << 1) ^ 0x9) & 0xF
            else:
                crc = (crc << 1) & 0xF
        return crc

    def _parse(self, bits, freq_hz):
        if len(bits) < 112:
            return None
        bits = [1 - b for b in bits]           # invert
        if bits_to_int(bits[0:4]) != 0:        # preamble nibble = 0x0
            return None
        # Three 32-bit packets at offsets 4, 40, 76
        packets = [bits[off:off + 32] for off in (4, 40, 76)
                   if off + 32 <= len(bits)]
        if not packets:
            return None
        # Majority vote across repetitions
        result = [1 if sum(p[i] for p in packets) * 2 >= len(packets) else 0
                  for i in range(32)]
        if result[:4] != [0, 0, 0, 1]:
            return None
        if self._crc4(result[:28]) != bits_to_int(result[28:32]):
            return None
        ch_raw   = bits_to_int(result[4:8])
        temp_raw = bits_to_int(result[8:18])
        battery  = result[25]
        ch = self._CH_MAP.get(ch_raw, ch_raw)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "channel":       ch,
            "temperature_C": round((temp_raw - 500) * 0.1, 1),
            "battery_ok":    not bool(battery),
            "mic":           "CRC",
        })


__all__ = ["PhilipsAJ3650"]
