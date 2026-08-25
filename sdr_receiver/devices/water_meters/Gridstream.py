"""@file
    Decoder for Gridstream RF devices produced by Landis & Gyr.

    Copyright (C) 2023 krvmk

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Landis & Gyr Gridstream Power Meters.

- Center Frequency: 915 MHz
- Frequency Range: 902-928 MHz
- Modulation: FSK-PCM (2-FSK, GFSK)
- Bitrates: 9600, 19200, 38400
- Preamble: 0xAAAA
- Syncword v4: 0b0000000001 0b0111111111
- Syncword v5: 0b0000000001 0b11111111111

Data layouts:
  Subtype 55: AAAAAA SSSS TT YY LLLL NN BBBBBBBBBB WWWWWWWWWW II MMMMMMMM KKKK EEEEEEEE KKKK KKKKKK CCCC KKKK XXXX KK
  Subtype D2: AAAAAA SSSS TT YY LL NN K--------K XXXX
  Subtype D5: AAAAAA SSSS TT YY LLLL NN DDDDDDDD EEEEEEEE II K----------K CCCC KKKK XXXX
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Gridstream(RawDecoder):
    """Landis & Gyr Gridstream electric/gas/water smart meter.

    FSK_PULSE_PCM.  Three bitrates sharing the same decoder logic:
      9600 baud:  chip=104 us, reset=20000 us
      19200 baud: chip=52 us,  reset=20000 us
      38400 baud: chip=22 us,  reset=20000 us
    V4 preamble: 0xAAAAAA00 5FF0 (36 bits).
    V5 preamble: 0xAAAAAA00 7FF8 (37 bits).
    UART 8N1 framing.  Subtypes: 0xD2 (1-byte length), 0x55/0xD5 (2-byte length).
    Subtype 0xD2 + CI 0x52 → AES-encrypted payload (no CRC validation).
    CRC-16/CCITT poly=0x1021 with provider-specific init (16 known utility entries).
    Key fields: networkID, location, provider, id, subtype, ci,
                wanaddress, destaddress, uptime, protoversion, framedata.
    """
    name = "Gridstream"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # Stub: Gridstream UART 8N1 framing and provider-specific CRC
        # not yet implemented.
        return None


__all__ = ["Gridstream"]
