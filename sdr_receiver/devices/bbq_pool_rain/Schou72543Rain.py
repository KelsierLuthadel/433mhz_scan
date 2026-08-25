"""Schou 72543 / Motonet MTX / MarQuant Rain Gauge  ported from rtl_433 C source.

Note: schou72543_rain.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from .._helpers import _bits_to_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Schou72543Rain(OOKPWMDecoder):
    """Schou 72543 / Motonet MTX / MarQuant Rain Gauge.

    OOK_PULSE_PWM, 64 bits (8 bytes data + 1 byte checksum implied).
    Layout: ID(16) STATUS(4) N(4) rain_lo(8) rain_hi(8) temp_lo(8) temp_hi(8) CHK(8).
    Checksum = running byte sum of bytes 0-6.
    """

    name     = "Schou-72543"
    short_us = 972.0
    long_us  = 2680.0
    reset_us = 2712.0
    n_bits   = 64

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 64:
            return None
        b = _bits_to_bytes(bits[:64])
        if len(b) < 8:
            return None
        chk_rx  = b[7]
        chk_cal = sum(b[:7]) & 0xFF
        if chk_cal == 0 or chk_rx != chk_cal:
            return None
        device_id      = (b[0] << 8) | b[1]
        battery_low    = (b[2] & 0x80) > 0
        msg_repeat     = (b[2] & 0x40) > 0
        msg_counter    = (b[2] & 0x0E) >> 1
        rain_mm        = round(((b[4] << 8) | b[3]) * 0.1, 1)
        temperature_f  = round((((b[6] << 8) | b[5]) - 900) * 0.1, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           device_id,
            "temperature_F": temperature_f,
            "rain_mm":      rain_mm,
            "battery_ok":   int(not battery_low),
            "msg_counter":  msg_counter,
            "msg_repeat":   int(msg_repeat),
        })


__all__ = ["Schou72543Rain"]
