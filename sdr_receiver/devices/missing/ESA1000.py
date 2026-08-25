"""ELV Energy Counter ESA 1000/2000.

Copyright (C) 2016 TylerDurden23, initial cleanup by Benjamin Larsson
Bug fixes / modifications for GIRA WST: D. Clawin (DCTRONIC Engineering)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

ELV Energy Counter ESA 1000/2000, GIRA EHZ.

ELV-ESA devices and Gira-EHZ share modulation and decryption.
Only CRC base is different.

ELVx000 data format (in German from FHEM source):

    ss                                         Sequenz und Sequenzwiederhohlung mit gesetzten hoechsten Bit
       dddd                                    Device
            cccc                               Code + Batterystate
                 tttttttt                      Gesamtimpulse
                          aaaa                 Impulse je Sequenz
                               zzzzzz          Zeitstempel seit Start des Adapters (ESA1000)
                                      kkkk     Impulse je kWh/m3

GIRA data format (bytes), reverse engineered:

    H II SS J PP TTT II UUUUUU KK CC

    - H: Header with sequence number
    - I: Dev ID
    - S: Status and device type (same for all Gira cc1e)
    - J: Single byte: 04
    - P: power in Watts
    - T: Total ticks since startup
    - I: Ticks since last message
    - U: Unknown, appears always zero
    - K: Ticks / kWh xor 1st byte of devid
    - C: CRC, sum of message bytes + 0xee11
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ESA1000(ManchesterDecoder):
    """ESA1000 / ESA2000 / GIRA Wetterstation energy monitor.
    OOK_PULSE_MANCHESTER_ZEROBIT, 160 or 176 bits.
    Fixed-value CRC: 0xF00F (ESA) or 0xEE11 (Gira).
    Multi-field protocol  stub pending full implementation.
    """
    name     = "ESA1000-ESA2000"
    chip_us  = 260.0
    reset_us = 3000.0
    n_bits   = 160
    _MAGIC_ESA  = 0xF00F
    _MAGIC_GIRA = 0xEE11

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return None


__all__ = ["ESA1000"]
