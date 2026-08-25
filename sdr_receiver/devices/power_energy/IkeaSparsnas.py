"""@file
    IKEA Sparsnäs Energy Meter Monitor.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

IKEA Sparsnäs Energy Meter Monitor.

The IKEA Sparsnäs consists of a display unit, and a sender unit. The sender unit
is placed by the energy meter with an IR photo sensor over the impulse diode.

Packet structure (20 bytes):
  0:  uint8_t length;        // Always 0x11
  1:  uint8_t sender_id_lo;  // Lowest byte of sender ID
  2:  uint8_t unknown;
  3:  uint8_t major_version; // Always 0x07
  4:  uint8_t minor_version; // Always 0x0E
  5:  uint32_t sender_id;    // ID of sender
  9:  uint16_t sequence;     // Sequence number
  11: uint16_t effect;       // Current effect usage
  13: uint32_t pulses;       // Total number of pulses
  17: uint8_t battery;       // Battery level, 0-100%
  18: uint16_t CRC;          // 16 bit CRC of bytes 0-17

The 128-bit payload is AES-128-CTR encrypted; decryption key derived from sender ID.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class IkeaSparsnas(RawDecoder):
    """IKEA Sparsnäs energy meter monitor (FSK_PULSE_PCM, ~37 kbps).

    Frame (20 bytes = 160 bits):
        byte 0    : length (0x11)
        byte 1    : sender ID low byte
        bytes 3-4 : protocol version (0x07 0x0E)
        bytes 5-8 : sender ID (32-bit)
        bytes 9-10: sequence number
        bytes 11-12: effect (watts)
        bytes 13-16: total pulses (32-bit)
        byte 17   : battery level (0-100 %)
        bytes 18-19: CRC-16 (poly 0x8005, init 0xFFFF)
    Note: 128-bit payload is AES-128-CTR encrypted; decryption key is derived
    from the sender ID.  Full decode requires the sender ID to be configured.
    """
    name = "IKEA-Sparsnas"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path + AES decryption required


__all__ = ["IkeaSparsnas"]
