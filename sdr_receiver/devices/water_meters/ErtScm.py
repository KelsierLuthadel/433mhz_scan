"""@file
    ERT Standard Consumption Message (SCM) sensors.

    Copyright (C) 2020 Benjamin Larsson.

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

ERT Standard Consumption Message (SCM) sensors.

https://github.com/bemasher/rtlamr
https://en.wikipedia.org/wiki/Encoder_receiver_transmitter
https://patentimages.storage.googleapis.com/df/23/d3/f0c33d9b2543ff/WO2007030826A2.pdf

96-bit Itron Standard Consumption Message protocol

Data layout:

    SAAA AAAA  AAAA AAAA  AAAA A
    iiR PPTT TTEE CCCC CCCC CCCC  CCCC CCCC  CCCC IIII  IIII IIII  IIII IIII  IIII XXXX XXXX XXXX  XXXX

- S - Sync bit
- A - Preamble
- i - ERT ID Most Significant bits
- R - Reserved
- P - Physical tamper
- T - ERT Type (4 and 7 are mentioned in the pdf)
- E - Encoder Tamper
- C - Consumption data
- I - ERT ID Least Significant bits
- X - CRC (polynomial 0x6F63)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ErtScm(ManchesterDecoder):
    """ERT SCM electricity/gas/water meter standard consumption message.

    OOK_PULSE_MANCHESTER_ZEROBIT, chip=30 us, reset=64 us.
    Packet: 96 bits (12 bytes).
    CRC-16 poly=0x6F63 init=0x0000, non-reflecting, over bytes[2:12] → result must be 0.
    Bit-level field layout:
      bits[0]     – sync bit
      bits[1:9]   – preamble (8 bits)
      bits[9:12]  – ERT ID MSBs (3 bits)
      bits[12]    – reserved
      bits[13:15] – physical tamper (2 bits)
      bits[15:19] – ERT type (4 bits)
      bits[19:21] – encoder tamper (2 bits)
      bits[21:45] – consumption data (24 bits)
      bits[45:77] – ERT ID LSBs (32 bits)
      bits[77:93] – CRC-16 (16 bits)
    """
    name = "ERT-SCM"
    chip_us = 30.0
    reset_us = 64.0
    n_bits = 96

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 96:
            return None

        # Pack to bytes for CRC calculation.
        data = bytes(bits_to_int(bits[i: i + 8]) for i in range(0, 96, 8))

        # Sanity: first 4 bytes must not all be zero.
        if not any(data[:4]):
            return None

        # CRC-16 over bytes[2:12] (includes stored CRC); result must be 0.
        crc_val = crc16(data[2:], poly=0x6F63, init=0x0000, ref_in=False, ref_out=False)
        if crc_val != 0:
            return None

        # Bit-level field extraction.
        ert_id_msb = bits_to_int(bits[9:12])
        physical_tamper = bits_to_int(bits[13:15])
        ert_type = bits_to_int(bits[15:19])
        encoder_tamper = bits_to_int(bits[19:21])
        consumption = bits_to_int(bits[21:45])
        ert_id_lsb = bits_to_int(bits[45:77])
        ert_id = (ert_id_msb << 32) | ert_id_lsb

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": ert_id,
            "physical_tamper": physical_tamper,
            "ert_type": ert_type,
            "encoder_tamper": encoder_tamper,
            "consumption_data": consumption,
            "mic": "CRC",
        })


__all__ = ["ErtScm"]
