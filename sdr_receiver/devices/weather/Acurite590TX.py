"""Acurite 590TX Temperature Sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Acurite590TX(OOKPPMDecoder):
    """Acurite 590TX Temperature Sensor.

    r_device: OOK_PULSE_PPM, short=500, long=1500, reset=3500.
    Message: 24 bits (3 bytes).
      b[0]       = battery(7), ID (6-0)
      b[1]       = channel (7-4), temp/hum high nibble (3-0)
      b[2]       = temp/hum low byte
    Value interpretation:
      raw12 = (b[1][3:0] << 8) | b[2]; unsigned.
      If 0 ≤ raw12 ≤ 100 → relative humidity (%).
      Else → sign-extend 12-bit, subtract 500, divide by 10 → °C.
    """
    name     = "Acurite-590TX"
    short_us = 500.0
    long_us  = 1500.0
    reset_us = 3500.0
    n_bits   = 24

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 24, 8))
        battery_ok = not bool(b[0] & 0x80)
        sensor_id  = b[0] & 0x7F
        channel    = (b[1] >> 4) & 0x0F
        raw12      = ((b[1] & 0x0F) << 8) | b[2]
        fields: dict = {"id": sensor_id, "channel": channel, "battery_ok": battery_ok}
        if 0 <= raw12 <= 100:
            fields["humidity"] = raw12
        else:
            # 12-bit signed, offset −500 (×0.1 °C)
            val = raw12 if raw12 < 2048 else raw12 - 4096
            temp_c = (val - 500) / 10.0
            if not -50.0 <= temp_c <= 70.0:
                return None
            fields["temperature_C"] = round(temp_c, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["Acurite590TX"]
