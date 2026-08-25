"""@file
    Blueline PowerCost Monitor protocol.

    Copyright (C) 2020 Justin Brzozoski

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

BlueLine Innovations Power Cost Monitor, tested with BLI-28000.

Much of the groundwork for this implementation was based on reading the source and notes from older
implementations, but this implementation was a fresh rewrite by Justin Brzozoski in 2020.

The IR-reader/sensor will transmit 3 bursts every ~30 seconds.  The low-level encoding is on/off
keyed pulse-position modulation (OOK_PPM).  The on pulses are always 0.5ms, while the off pulses
are either 0.5ms for logic 1 or 1.0ms for logic 0.  Each burst is 32 bits long.

The basic layout of all bursts is as follows:
- First is a 1 byte header, which is always the value 0xFE.
- Second is a 2 byte payload, which is interpreted differently based on the two lowest bits of the
  first byte.
- Finally is a 1 byte CRC, calculated across the 2 payload bytes (not the header).

The CRC is a CRC-8-ATM with polynomial 100000111.

There are 4 message types indicated by the 2 lowest bits of the first payload byte:
- 0: ID message
- 1: power message (gap between impulses in ms)
- 2: temperature/status message
- 3: energy message (impulse accumulator)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BluelinePowerCost(OOKPPMDecoder):
    """Blueline PowerCost Monitor energy sensor.

    Modulation: OOK_PULSE_PPM.
    Timings in the C source: short gap 500 µs = logic 1, long gap 1000 µs = logic 0.
    This is inverted from the base-class convention (short gap = 0), so short_us and
    long_us are swapped here so that pulses_to_bits_ppm assigns the correct values.

    Frame (32 bits, MSB first):
        byte 0  : header 0xFE
        bytes 1-2: payload (little-endian)
        byte 3  : CRC-8/ATM (poly 0x07, init 0x00)
    Message types (byte-1 bits 1-0): 0=ID, 1=power gap ms, 2=temp/status, 3=energy.
    """
    name     = "Blueline-PowerCost"
    # Swapped: physically 500 µs gap = bit 1; 1000 µs gap = bit 0.
    short_us = 1_000.0
    long_us  = 500.0
    reset_us = 8_000.0
    n_bits   = 32

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 32:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 32, 8)]
        if b[0] != 0xFE:
            return None
        msg_type = b[1] & 0x03
        fields: dict = {"msg_type": msg_type}
        if msg_type == 0x00:            # ID message  CRC is directly verifiable
            if crc8(bytes(b[:3]), poly=0x07) != b[3]:
                return None
            fields["id"] = b[1] | (b[2] << 8)
        elif msg_type == 0x01:          # power: gap between impulses (ms)
            fields["gap"] = b[1] | (b[2] << 8)
        elif msg_type == 0x02:          # temperature / battery status
            fields["battery_ok"] = int(bool((b[1] >> 7) & 1))
            fields["flags"]       = b[1] & 0x7F
            fields["temperature_C"] = round(0.436 * b[2] - 30.36, 1)
        elif msg_type == 0x03:          # energy impulse accumulator
            fields["impulses"] = b[1] | (b[2] << 8)
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["BluelinePowerCost"]
