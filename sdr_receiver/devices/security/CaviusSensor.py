"""Cavius smoke, heat and water detector.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Cavius smoke, heat and water detector decoder.

The alarm units use HopeRF RF69 chips on 869.67 MHz, FSK modulation, 4800 bps.
They seem to use 'Cavi' as a sync word on the chips.
Everything after the sync word is Manchester coded.
The unpacked payload is 11 bytes long structured as follows:

    NNNNMMCSSSS

- N: Network ID (Device ID of the Master device)
- M: Message bytes. Second byte is the first byte inverted (0xFF ^ M)
- C: CRC-8 (Maxim type) of NNNNMM (the first 6 bytes in the payload)
- S: Sending device ID

Message bits as far as we can tell:

- 0x80: PAIRING
- 0x40: TEST
- 0x20: ALARM
- 0x10: WARNING
- 0x08: BATTLOW
- 0x04: MUTE
- 0x02: UNKNOWN2
- 0x01: UNKNOWN1

Sometimes the receiver samplerate has to be at 250ksps to decode properly.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class CaviusSensor(RawDecoder):
    """Cavius smoke/heat/water alarm (FSK_PULSE_PCM, 206 µs chip).

    Full FSK demodulation required; returns None until FSK pipeline feeds
    demodulated chips into this decoder.
    """

    name = "Cavius"

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["CaviusSensor"]
