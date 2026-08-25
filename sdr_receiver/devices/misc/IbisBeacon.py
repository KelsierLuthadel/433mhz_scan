"""IBIS vehicle information beacon.

Copyright (C) 2017 Christian W. Zuckschwerdt <zany@triq.net>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

IBIS vehicle information beacon.
(used in public transportation)

The packet is 28 manchester encoded bytes with a Preamble of 0xAAB and
16-bit CRC, containing a company ID, vehicle ID, (door opening) counter,
and various flags.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class IbisBeacon(ManchesterDecoder):
    """IBIS beacon (bus/tram vehicle ID beacon)."""
    name     = "IBIS-Beacon"
    chip_us  = 30.0
    reset_us = 100.0
    n_bits   = 232    # 28 bytes data + 12-bit preamble overhead

    def _parse(self, bits, freq_hz):
        if len(bits) < 224:
            return None
        # Search for preamble 0xAAB (12 bits) within first 26 bit positions
        start = -1
        for i in range(min(26, len(bits) - 12)):
            if bits_to_int(bits[i:i + 12]) == 0xAAB:
                start = i + 12
                break
        if start < 0 or start + 224 > len(bits):
            return None
        msg_bits = bits[start:start + 224]
        msg = bytes(bits_to_int(msg_bits[i:i + 8]) for i in range(0, 224, 8))
        # CRC-16 over first 26 bytes, poly=0x8005, init=0x0000, no reflection
        crc_calc = crc16(msg[:26], poly=0x8005, init=0x0000,
                         ref_in=False, ref_out=False)
        crc_recv = (msg[26] << 8) | msg[27]
        if crc_calc != crc_recv:
            return None
        vehicle_id = ((msg[5] & 0x0F) << 12) | (msg[6] << 4) | ((msg[7] & 0xF0) >> 4)
        counter    = (msg[20] << 24) | (msg[21] << 16) | (msg[22] << 8) | msg[23]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "vehicle_id": vehicle_id,
            "counter":    counter,
            "code":       msg.hex(),
            "mic":        "CRC",
        })


__all__ = ["IbisBeacon"]
