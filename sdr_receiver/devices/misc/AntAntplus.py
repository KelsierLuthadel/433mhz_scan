"""ANT and ANT+ decoder.

Copyright (C) 2022 Roberto Cazzaro <https://github.com/robcazzaro>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

ANT and ANT+ decoder.

ANT and ANT+ communication standards are defined by a division of Garmin
https://www.thisisant.com/ and used widely for low power devices.
The ANT radio transmits for less than 150 us per message, allowing a single
channel to be divided into hundreds of time slots and avoiding collisions.
ANT and ANT+ devices use a modified Shockburst protocol, in the 2.4GHz ISM band,
with 160kHz deviation and 1Mbps data rates, GFSK encoded. The low level
layer is not documented anywhere. ANT chips use an 8 byte key to generate a 2 byte
network ID using an unspecified algorithm. Valid keys are only assigned by Garmin
and require specific licensing terms (and in some cases a payment)
ANT+ uses the basic ANT message structure but is a managed network with a specific
network key and defined device types, each sending "data pages" of 8 bytes with
specific data for the device type. Most ANT+ devices are sports focused like
heart rate monitors, bicycle sensors, or environmental sensors.

Please note that unlike most devices in the rtl_433 repository, ANT+ devices
operate in the ISM band between 2.4GHz and 2.5GHz. Decoding these signals
requires an SDR capable of operating above 2.4GHz (e.g. PlutoSDR) or the
use of a downconverter for rtl_sdr.

To avoid excessive warnings when running with default 250k sampling rate,
the decoder is disabled by default.

The payload is 18 bytes long structured as follows:

    PNNDDTXLPPPPPPPPCC

- P: Preamble: either 0x55 or 0xAA, depending on the value of first bit of the next byte
- N: Network key, assume LSB first (ANT+ uses 0xc5a6, most invalid keys 0x255b)
- D: Device number, 16 bit. LSB first
- X: Transmission type
- L: ANT payload length including CRC
- P: 8 byte ANT or ANT+ payload
- C: 16 bit CRC (CRC-16/CCITT-FALSE)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AntAntplus(RawDecoder):
    """ANT and ANT+ devices  FSK PCM (requires 4 MS/s)."""
    name = "ANT-ANTplus"

    def decode(self, pulses, freq_hz):
        return None


__all__ = ["AntAntplus"]
