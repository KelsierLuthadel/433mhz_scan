"""Auriol 4-LD6654 temperature/humidity/rain sensor (Lidl).

433.92 MHz OOK-PPM, short=1000 us, long=2000 us, reset=4000 us.
52 bits, no checksum; validated by separator nibble == 0xF and flag bit == 0.

Frame layout (52 bits, MSB first):
  [7:0]   ID        8-bit  random, resets on battery change
  [8]     Battery   1=OK  0=LOW
  [9]     Flag      must be 0
  [11:10] Channel   2-bit (add 1 for display)
  [23:12] Temp      12-bit two's complement, x0.1 degC
  [27:24] Separator must be 0xF
  [35:28] Humidity  8-bit  %RH
  [51:36] Rain      16-bit tipping bucket count, x1.16 mm
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Auriol4LD6654(OOKPPMDecoder):
    """Auriol 4-LD6654 outdoor weather sensor with rain gauge."""
    name     = "Auriol-4LD6654"
    short_us = 1000.0
    long_us  = 2000.0
    reset_us = 4000.0
    n_bits   = 52

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 52:
            return None

        flag = bits[9]
        if flag != 0:
            return None

        sep = bits_to_int(bits[24:28])
        if sep != 0xF:
            return None

        device_id = bits_to_int(bits[0:8])
        battery_ok = bits[8] == 1
        channel = bits_to_int(bits[10:12]) + 1

        temp_raw = bits_to_int(bits[12:24])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c = temp_raw * 0.1

        if not -50.0 <= temp_c <= 80.0:
            return None

        humidity = bits_to_int(bits[28:36])
        if not 1 <= humidity <= 100:
            return None

        rain_count = bits_to_int(bits[36:52])
        rain_mm = round(rain_count * 1.16, 2)

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    int(battery_ok),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
            "rain_mm":       rain_mm,
        })


__all__ = ["Auriol4LD6654"]
