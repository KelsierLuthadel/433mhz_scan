"""Bresser Thermo-Hygro Sensor 3-CH / compatible clones (OOK PWM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Bresser3CH(OOKPWMDecoder):
    """Bresser Thermo-Hygro Sensor 3-CH / compatible clones (OOK PWM).

    Protocol (40 bits, all bytes transmitted inverted / active-low):
      [id:8] [bat:1][ch:2][pad:1][temp_hi:4] [temp_lo:8] [hum:8] [chk:8]
    Temperature raw value is in tenths of °F, offset by 900 (i.e. 900 = 90.0 °F).
    Checksum: (b0+b1+b2+b3) mod 256 == b4  (after inversion).
    """
    name     = "Bresser-3CH"
    short_us = 250.0
    long_us  = 500.0
    reset_us = 1_250.0
    n_bits   = 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Recover bytes and invert (protocol inverts all bits on air)
        raw = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8))
        b = bytes(x ^ 0xFF for x in raw)

        # Additive checksum
        if (b[0] + b[1] + b[2] + b[3] - b[4]) & 0xFF != 0:
            return None

        device_id  = b[0]
        battery_ok = not bool(b[1] & 0x80)
        channel    = (b[1] & 0x30) >> 4
        temp_raw   = ((b[1] & 0x0F) << 8) | b[2]
        temp_f     = (temp_raw - 900) * 0.1   # tenths of °F, offset 900
        humidity   = b[3]

        # Sanity (channel 0 is invalid; humidity and temperature ranges)
        if channel == 0 or humidity > 100 or not (-20.0 <= temp_f <= 160.0):
            return None

        temp_c = (temp_f - 32.0) * 5.0 / 9.0

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["Bresser3CH"]
