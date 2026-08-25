"""Kerui PIR / Contact Sensor.

Copyright (C) 2016 Karl Lattimer

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Kerui PIR / Contact Sensor.

Such as
http://www.ebay.co.uk/sch/i.html?_from=R40&_trksid=p2050601.m570.l1313.TR0.TRC0.H0.Xkerui+pir.TRS0&_nkw=kerui+pir&_sacat=0

also tested with:
- KERUI D026 Window Door Magnet Sensor Detector (433MHz) https://fccid.io/2AGNGKR-D026
  events: open / close / tamper / battery low (below 5V of 12V battery)
- Water leak sensor WD51
- Mini Pir P831

Note: simple 24 bit fixed ID protocol (x1527 style) and should be handled by the flex decoder.
There is a leading sync bit with a wide gap which runs into the preceding packet, it's ignored as 25th data bit.

There are slight timing differences between the older sensors and new ones like Water leak sensor WD51 and Mini Pir P831.
Long: 860-1016 us, short: 304-560 us, older sync: 480 us, newer sync: 340 us,
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


_KERUI_CMD: dict[int, str] = {
    0xA: "motion", 0xE: "open", 0x7: "closed",
    0xB: "tamper", 0x5: "water", 0xF: "battery_low",
}


class KeruiSensor(OOKPWMDecoder):
    """Kerui wireless PIR / door / water sensor (OOK_PULSE_PWM, 420/960 µs, 25 bits)."""

    name      = "Kerui"
    short_us  = 420.0
    long_us   = 960.0
    reset_us  = 9900.0
    n_bits    = 25
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 25:
            return None
        b = [x ^ 1 for x in bits[:24]]   # invert (short=1, long=0 physically)
        b0 = bits_to_int(b[0:8])
        b1 = bits_to_int(b[8:16])
        b2 = bits_to_int(b[16:24])
        sensor_id = (b0 << 12) | (b1 << 4) | (b2 >> 4)
        if sensor_id == 0:
            return None
        cmd = b2 & 0x0F
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         f"{sensor_id:05X}",
            "cmd":        _KERUI_CMD.get(cmd, f"unknown(0x{cmd:X})"),
            "motion":     int(cmd == 0xA),
            "opened":     int(cmd == 0xE),
            "tamper":     int(cmd == 0xB),
            "water":      int(cmd == 0x5),
            "battery_ok": int(cmd != 0xF),
        })


__all__ = ["KeruiSensor"]
