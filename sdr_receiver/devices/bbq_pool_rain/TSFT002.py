"""TS-FT002 Wireless Ultrasonic Tank Liquid Level Meter  ported from rtl_433 C source.

Note: tsft002.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from .._helpers import _bits_to_bytes, _reverse8
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TSFT002(OOKPPMDecoder):
    """TS-FT002 Wireless Ultrasonic Tank Liquid Level Meter With Temperature Sensor.

    OOK_PULSE_PPM (bits LSB-first), 72 bits = 9 bytes.
    Preamble byte 0xfa (0x5f before reflect), message type 0x11.
    XOR checksum over all 9 bytes = 0.
    Depth in cm, temperature in C (offset 400, scale 10).
    """

    name     = "TS-FT002"
    short_us = 464.0
    long_us  = 948.0
    reset_us = 2000.0
    n_bits   = 72

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 70:
            return None
        n = len(bits)
        # Handle 70, 71, or 72 bits (C code handles offsets)
        b = bytearray(9)
        if n >= 72:
            raw = _bits_to_bytes(bits[:72])
            b[:] = raw[:9]
        elif n == 71:
            raw = _bits_to_bytes(bits[7:71])
            b[1:] = raw[:8]
            b[0] = bits_to_int(bits[:7]) << 1  # approximate
        else:  # 70
            raw = _bits_to_bytes(bits[6:70])
            b[1:] = raw[:8]
            b[0] = 0x80 | (bits_to_int(bits[:6]) << 2)
        # XOR checksum
        xor = 0
        for byte in b:
            xor ^= byte
        if xor != 0:
            return None
        # Reflect bytes for actual field extraction
        rb = bytes(_reverse8(x) for x in b[:8])
        id_      = rb[1]
        type_    = rb[2]
        if type_ != 0x11:
            return None
        depth    = (rb[3] << 4) | (rb[4] & 0x0F)
        batt_low = rb[4] >> 4
        transmit = rb[5] >> 4
        temp_raw = (rb[6] << 4) | (rb[5] & 0x0F)
        temp_c   = round((temp_raw - 400) * 0.1, 1)
        if (transmit & 0x07) == 0x07:
            transmit = 5
        elif (transmit & 0x08) == 0x08:
            transmit = 30
        elif transmit == 0:
            transmit = 180
        else:
            transmit = 0
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           id_,
            "depth_cm":     depth,
            "temperature_C": temp_c,
            "transmit_s":   transmit,
            "flags":        batt_low,
        })


__all__ = ["TSFT002"]
