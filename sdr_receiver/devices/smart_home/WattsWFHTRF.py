"""Watts WFHT-RF wireless thermostat (Manchester variant) decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc8, crc16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class WattsWFHTRF(ManchesterDecoder):
    """Watts WFHT-RF wireless thermostat (Manchester variant).

    OOK_PULSE_MANCHESTER_ZEROBIT, chip=460 µs, reset=900 µs.
    128 data bits after sync word.
    Fields: mode[8] | id[24] | temp[16] | setpoint[16] | heat_call[8] | crc8[8] | crc16[16].
    CRC-8: poly=0xE6, init=0x00, over bytes 0-12, XOR 0xBE.
    CRC-16/CMS: poly=0x8005, init=0xFFFF, over bytes 0-13.
    """
    name     = "Watts-WFHT-RF"
    chip_us  = 460.0
    reset_us = 900.0
    n_bits   = 128

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 128:
            return None
        b = [bits_to_int(bits[i : i + 8]) for i in range(0, 128, 8)]
        # CRC-8
        crc8_calc = crc8(bytes(b[0:13]), poly=0xE6, init=0x00) ^ 0xBE
        if crc8_calc != b[13]:
            return None
        # CRC-16/CMS
        crc16_calc = crc16(bytes(b[0:14]), poly=0x8005, init=0xFFFF,
                           ref_in=False, ref_out=False)
        crc16_rx   = (b[14] << 8) | b[15]
        if crc16_calc != crc16_rx:
            return None
        mode      = b[4]
        device_id = (b[5] << 16) | (b[6] << 8) | b[7]
        temp_raw  = (b[8] << 8) | b[9]
        setp_raw  = (b[10] << 8) | b[11]
        heat_call = b[12]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "temperature_C": round(temp_raw / 10.0, 1),
            "setpoint_C":    round(setp_raw / 10.0, 1),
            "heat_call":     heat_call > 0,
            "pairing":       int(bool(mode & 0x01)),
        })


__all__ = ["WattsWFHTRF"]
