"""@file
    Decoder for Voltcraft EnergyCount 3000 (ec3k, sold by Conrad), tested with RT-110

    Copyright (C) 2025 Michael Dreher <michael(a)5dot1.de>, nospam2000 at github.com

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Decoder for Voltcraft EnergyCount 3000 (ec3k, sold by Conrad), tested with RT-110

The bit time is 50 us. The device transmits every 5 seconds (if there is a change in power
consumption) or every 30 minutes (if there is no change). It uses BFSK modulation.

The used chip is probably a AX5042 from On Semiconductor. HDLC mode follows High-Level Data
Link Control (HDLC, ISO 13239) protocol. The packet is NRZI encoded, with bit stuffing (a 0 is
inserted after 5 consecutive 1 bits). The packet is framed by 0x7E bytes.
The CRC polynomial is 0x8408 (reverse of CRC-16-CCITT), initial value 0xFFFF.

List of known compatible devices:
- Voltcraft EnergyCount 3000 (ec3k, Item No. 12 53 53)
- Technoline Cost Control RT-110, EAN 4029665006208
- Velleman (type NETBESEM4)
- La Crosse Technology Remote Cost Control Monitor (type RS3620)

Fields decoded: id, power (W), energy (Wh), time_total (s), time_on (s),
power_max (W), reset_counter, flags, crc.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class EC3k(RawDecoder):
    """Voltcraft EnergyCount 3000 (FSK_PULSE_PCM, 20 kbps NRZI + HDLC bit-stuffing).

    Complex HDLC framing: NRZI → bit destuffing → 0x7E frame markers.
    41-byte payload including 16-bit CRC-16/IBM-SDLC (poly 0x8408, init 0xFFFF).
    Fields: id, power (W), energy (Wh), time_total (s), time_on (s),
            power_max (W), reset_counter, flags.
    """
    name = "EC3k"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK path only


__all__ = ["EC3k"]
