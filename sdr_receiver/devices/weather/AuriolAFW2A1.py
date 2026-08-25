"""Auriol AFW2A1 temperature/humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _sign16_top12
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AuriolAFW2A1(OOKPPMDecoder):
    """Auriol AFW2A1 temperature/humidity sensor."""
    name     = "Auriol-AFW2A1"
    short_us = 576.0
    long_us  = 1_536.0
    reset_us = 3_954.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        b     = [bits_to_int(bits[i:i + 8]) for i in range(0, 32, 8)]  # b[0..3]
        b4hi  = bits_to_int(bits[32:36])  # upper nibble of b[4]

        # Fixed nibble check
        if (b[3] >> 4) != 0xA:
            return None

        device_id  = b[0]
        battery_ok = (b[1] >> 7) & 1
        tx_button  = (b[1] >> 6) & 1
        channel    = ((b[1] >> 4) & 0x03) + 1

        t16    = ((b[1] & 0x0F) << 12) | (b[2] << 4)
        temp_c = _sign16_top12(t16) * 0.1

        humidity = ((b[3] & 0x0F) << 4) | b4hi

        if not -50.0 <= temp_c <= 80.0:
            return None
        if not 0 <= humidity <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "button":        tx_button,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["AuriolAFW2A1"]
