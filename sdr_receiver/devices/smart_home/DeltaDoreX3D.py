"""Decoder for DeltaDore X3D devices.

Copyright (C) 2021 Sven Fabricius <sven.fabricius@livediesel.de>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Decoder for DeltaDore X3D devices.

Note: work in progress

- Modulation: FSK PCM
- Frequency: 868.95MHz
- 25 us bit time
- 40000 baud
- based on Semtech SX1211
- manual CRC

Payload format:
- Preamble          {32} 0xaaaaaaaa
- Syncword          {32} 0x8169967e
- Length            {8}
- Header            {n}
- Msg Payload       {n}
- CRC16             {16}

To get raw data:

    ./rtl_433 -f 868.95M -X 'n=DeltaDore,m=FSK_PCM,s=25,l=25,r=800,preamble=aa8169967e'
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class DeltaDoreX3D(RawDecoder):
    """DeltaDore X3D 868 MHz home-automation system.

    FSK_PULSE_PCM, chip=25 µs, reset=800 bits.
    Preamble: 0xaaaaaaaa | syncword: 0x8169967e | length[8] | payload | CRC-16.
    CRC-16/CCITT: poly=0x1021, init=0x0000.  Data is CCITT-whitened.
    Stub: FSK demodulation not supported in OOK pipeline.
    """
    name = "DeltaDore-X3D"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK demodulation


__all__ = ["DeltaDoreX3D"]
