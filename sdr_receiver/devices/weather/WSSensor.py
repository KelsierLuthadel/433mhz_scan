"""Hyundai WS SENZOR outdoor temperature sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _sign16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class WSSensor(OOKPPMDecoder):
    """Hyundai WS SENZOR outdoor temperature sensor."""
    name     = "WS-Senzor"
    short_us = 1_000.0
    long_us  = 2_000.0
    reset_us = 4_400.0
    n_bits   = 24

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 24:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 24, 8))

        # Reject all-zero / all-ones frames
        if (b[0] == 0x00 and b[1] == 0x00) or (b[0] == 0xFF and b[1] == 0xFF):
            return None

        # b[0] = T[11:4]; b[1][7:4] = T[3:0]; b[1][3] = BAT; b[1][2] = START; b[1][1:0] = CH
        temp_c     = (_sign16((b[0] << 8) | b[1]) >> 4) * 0.1
        battery_ok = (b[1] >> 3) & 1
        cc         = b[1] & 0x3
        channel    = cc + 1       # 0-indexed → 1–3
        sensor_id  = b[2]

        if cc > 2:                # channel 3 not valid for this sensor
            return None
        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["WSSensor"]
