"""Solight TE44 / TE66 and compatible 36-bit temperature sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _nexus_crc_ok(bits: list[int]) -> bool:
    """CRC-8 (poly=0x31, init=0x6C) over 4 bytes from a 36-bit Nexus-family packet.

    The first 32 bits form data bytes; bits[28:36] are the 8-bit CRC.
    data[3] intentionally contains the 0xF constant nibble in its high nibble
    and the first CRC nibble in its low nibble  this mirrors how rtl_433's
    C decoder builds its byte array from the 36-bit bitbuffer row.
    """
    data = bytes(bits_to_int(bits[i:i+8]) for i in range(0, 32, 8))
    crc_recv = bits_to_int(bits[28:36])
    return crc8(data, 0x31, 0x6C) == crc_recv


class SolightTE44(OOKPPMDecoder):
    """Solight TE44 / TE66 and compatible 36-bit temperature sensor."""
    name     = "Solight-TE44"
    short_us = 972.0
    long_us  = 1932.0
    reset_us = 6000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        const_nibble = bits_to_int(bits[24:28])
        if const_nibble != 0xF:
            return None
        if not _nexus_crc_ok(bits):
            return None
        device_id  = bits_to_int(bits[0:8])
        battery_ok = bool(bits[8])
        channel    = bits_to_int(bits[10:12]) + 1
        temp_raw   = bits_to_int(bits[12:24])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c = temp_raw / 10.0
        if not -50.0 <= temp_c <= 80.0:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id, "channel": channel, "battery_ok": battery_ok,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["SolightTE44"]
