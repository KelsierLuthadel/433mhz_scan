"""@file
    Revolt NC-5462 Energy Meter.

    Copyright (C) 2023 Nicolai Hess

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Revolt NC-5462 Energy Meter.

- Sends on 433.92 MHz.
- Pulse Width Modulation with startbit/delimiter

Two Modes:

Normal data mode:
- 105 pulses
- first pulse sync
- 104 data pulses (11 times 8 bit data + 8 bit checksum + 8 bit unknown)
- 11 byte data: detect flag, id, voltage, current, frequency, power, power factor, energy

Register mode (after pushing button on energy meter):
Same 104 data pulses as in data mode, but first bit high and multiple rows of data.

Pulses:
- sync ~ 10 ms high / 280 us low
- 1-bit ~ 320 us high / 160 us low
- 0-bit ~ 180 us high / 160 us low
- message end 180 us high / 100 ms low
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class RevoltNC5462(OOKPWMDecoder):
    """Revolt NC-5462 smart plug power meter.

    Modulation: OOK_PULSE_PWM.  short 200 µs = 0, long 320 µs = 1.
    A ~10 ms sync pulse precedes data; max_offset handles alignment.
    Frame (104 bits = 13 bytes):
        byte 0   : button flag (bit 7), device ID high (bits 6-0)
        byte 1   : device ID low
        byte 2   : voltage (V, direct)
        bytes 3-4: current (×0.01 A)
        byte 5   : mains frequency (Hz, direct)
        bytes 6-7: active power (×0.1 W)
        byte 8   : power factor (×0.01)
        bytes 9-10: energy (×0.01 kWh)
        byte 11  : checksum = sum(bytes 0-10) mod 256
        byte 12  : unknown
    """
    name     = "Revolt-NC5462"
    short_us = 200.0
    long_us  = 320.0
    reset_us = 1_000.0   # C reset_limit is a gap limit; set above long pulse width
    n_bits   = 104
    max_offset = 8        # absorb the leading 10 ms sync pulse

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 104:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 104, 8))
        if sum(b[:11]) & 0xFF != b[11]:
            return None
        button    = bool(b[0] >> 7)
        device_id = ((b[0] & 0x7F) << 8) | b[1]
        voltage_v = float(b[2])
        current_a = ((b[3] << 8) | b[4]) * 0.01
        freq_meas = float(b[5])
        power_w   = ((b[6] << 8) | b[7]) * 0.1
        pf        = b[8] * 0.01
        energy    = ((b[9] << 8) | b[10]) * 0.01
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           device_id,
            "voltage_V":    round(voltage_v, 1),
            "current_A":    round(current_a, 2),
            "frequency_Hz": freq_meas,
            "power_W":      round(power_w, 1),
            "power_factor": round(pf, 2),
            "energy_kWh":   round(energy, 2),
            "button":       int(button),
            "mic":          "CHECKSUM",
        })


__all__ = ["RevoltNC5462"]
