"""TPMS TyreGuard 400 from Davies Craig.

Copyright (C) 2022 R ALVERGNAT

TyreGuard 400 TPMS decoder.

TPMS TyreGuard 400 from Davies Craig operates at 434.1 MHz using ASK modulation
with Manchester Code. The protocol transmits 22-byte packets containing sensor
identification, tire pressure in PSI, temperature in degrees Celsius (offset by
+40), and status flags indicating pressure leaks and peering requests. The packet
includes a CRC checksum using polynomial 0x31 across the first 80 bits. Pressure
measurements combine an 8-bit value with three flag bits for full range
representation. Temperature readings require subtracting 40 from the transmitted
byte value. Peering new sensors requires setting specific flag bits to indicate
the pairing mode.

Source: tpms_tyreguard400.c
Modulation: OOK_PULSE_MANCHESTER_ZEROBIT, chip=~100 us
88 decoded bits. Preamble: 0xfd5fd5f (28 bits = 7 nibbles).
bits[28:56]  ID (28-bit)
bits[56:64]  pressure low byte (kPa low 8 bits)
bits[64:72]  temperature raw (- 40 deg C)
bits[72:80]  flags: bits[4:2]=pressure_MSBs, bit3=ack_leak, bits[7:6]=leak
bits[80:88]  CRC-8 poly=0x31 init=0xdd over first 80 bits (10 bytes)
pressure_kPa = pressure_low | ((flags>>2)&0x7)<<8
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
from ._helpers import _bits_to_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsTyreguard400(ManchesterDecoder):
    """TyreGuard 400 TPMS  OOK_PULSE_MANCHESTER_ZEROBIT, chip≈100 µs.

    88 decoded bits.  Preamble: 0xfd5fd5f (28 bits = 7 nibbles).
    bits[28:56]  ID (28-bit)
    bits[56:64]  pressure low byte (kPa low 8 bits)
    bits[64:72]  temperature raw (- 40 deg C)
    bits[72:80]  flags: bits[4:2]=pressure_MSBs, bit3=ack_leak, bits[7:6]=leak
    bits[80:88]  CRC-8 poly=0x31 init=0xdd over first 80 bits (10 bytes)
    pressure_kPa = pressure_low | ((flags>>2)&0x7)<<8
    """

    name     = "TyreGuard400"
    chip_us  = 100.0
    reset_us = 500.0
    n_bits   = 88

    # fmt: off
    _PREAMBLE = [
        1, 1, 1, 1, 1, 1, 0, 1,   # 0xfd
        0, 1, 0, 1, 1, 1, 1, 1,   # 0x5f
        1, 1, 0, 1, 0, 1, 0, 1,   # 0xd5
        1, 1, 1, 1,                # 0xf  (lower nibble of 0xfd5fd5f)
    ]
    # fmt: on

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 88:
            return None
        if bits[:28] != self._PREAMBLE:
            return None
        sensor_id    = bits_to_int(bits[28:56])
        pressure_lo  = bits_to_int(bits[56:64])
        temp_raw     = bits_to_int(bits[64:72])
        flags        = bits_to_int(bits[72:80])
        crc_read     = bits_to_int(bits[80:88])
        data = _bits_to_bytes(bits[:80])
        if len(data) < 10:
            return None
        if crc8(data[:10], poly=0x31, init=0xdd) != crc_read:
            return None
        pressure_kpa = pressure_lo | (((flags >> 2) & 0x7) << 8)
        temp_c       = temp_raw - 40
        ack_leak     = bool(flags & 0x08)
        leak         = (flags >> 6) & 0x3
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           format(sensor_id, "07x"),
            "pressure_kPa": pressure_kpa,
            "temperature_C": temp_c,
            "flags":        format(flags, "02x"),
            "ack_leak":     ack_leak,
            "leak":         leak,
        })


__all__ = ["TpmsTyreguard400"]
