"""Burnhard BBQ wireless meat thermometer  ported from rtl_433 C source.

Note: burnhard.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _lfsr_digest8_reflect(data: bytes, gen: int, key: int) -> int:
    """Galois LFSR MAC, LSB-first (reflected). Matches rtl_433 lfsr_digest8_reflect."""
    s = 0
    for byte in data:
        for i in range(8):          # LSB first
            if (byte >> i) & 1:
                s ^= key
            if key & 1:
                key = (key >> 1) ^ gen
            else:
                key >>= 1
    return s


class BurnhardBBQ(OOKPWMDecoder):
    """Burnhard BBQ wireless meat thermometer.

    Modulation: OOK_PULSE_PWM.  short 240 µs = 0, long 484 µs = 1.
    A sync pulse (~840 µs) precedes the data burst; max_offset skips it.
    CRC: lfsr_digest8_reflect(b[0:9], gen=0x31, key=0xF4) == b[9].

    Frame (80 bits = 10 bytes):
        byte 0  : device ID
        byte 1  : settings  bit7=temp_alarm, bit6=timer_alarm,
                             bit4=timer_active, bits2-0=channel
        byte 2  : unused
        bytes 3-4: timer (BCD: b[3]=hours, b[4]=minutes)
        byte 5  : meat type (upper nibble) | taste level (lower nibble)
        bytes 6-8: temperatures as two 12-bit values (packed)
                   setpoint_raw = (b[6]<<4) | (b[7]>>4)
                   temp_raw     = ((b[7]&0xF)<<8) | b[8]
                   Celsius      = (raw - 500) / 10.0
        byte 9  : CRC (LFSR digest)
    """
    name     = "Burnhard-BBQ"
    short_us = 240.0
    long_us  = 484.0
    reset_us = 1_000.0   # above sync pulse (~840 µs); sync excluded from data
    n_bits   = 80
    max_offset = 3

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 80:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 80, 8))
        if _lfsr_digest8_reflect(b[:9], gen=0x31, key=0xF4) != b[9]:
            return None
        device_id    = b[0]
        temp_alarm   = bool((b[1] >> 7) & 1)
        timer_alarm  = bool((b[1] >> 6) & 1)
        timer_active = bool((b[1] >> 4) & 1)
        channel      = b[1] & 0x07
        timer_h      = (b[3] >> 4) * 10 + (b[3] & 0xF)
        timer_m      = (b[4] >> 4) * 10 + (b[4] & 0xF)
        timer        = timer_h * 60 + timer_m   # total minutes
        meat         = (b[5] >> 4) & 0xF
        taste        = b[5] & 0xF
        setpoint_raw = (b[6] << 4) | (b[7] >> 4)
        temp_raw     = ((b[7] & 0x0F) << 8) | b[8]
        setpoint_c   = round((setpoint_raw - 500) / 10.0, 1)
        temp_c       = round((temp_raw     - 500) / 10.0, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":               device_id,
            "channel":          channel,
            "temperature_C":    temp_c,
            "setpoint_C":       setpoint_c,
            "temperature_alarm": int(temp_alarm),
            "timer":            timer,
            "timer_active":     int(timer_active),
            "timer_alarm":      int(timer_alarm),
            "meat":             meat,
            "taste":            taste,
        })


__all__ = ["BurnhardBBQ"]
