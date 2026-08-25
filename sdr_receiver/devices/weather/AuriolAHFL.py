"""Auriol AHFL 433B2 IPX4 temperature/humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _sign16_top12
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AuriolAHFL(OOKPPMDecoder):
    """Auriol AHFL 433B2 IPX4 temperature/humidity sensor."""
    name     = "Auriol-AHFL"
    short_us = 2_100.0
    long_us  = 4_150.0
    reset_us = 9_150.0
    n_bits   = 42

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 42:
            return None
        b     = [bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8)]  # b[0..4]
        last2 = bits_to_int(bits[40:42])

        # Structural checks
        if (b[4] & 0xF0) != 0x40 or (b[3] & 0x01) != 0:
            return None

        # Nibble-sum checksum (6-bit)
        nibble_sum = (
            (b[0] & 0xF) + (b[0] >> 4) +
            (b[1] & 0xF) + (b[1] >> 4) +
            (b[2] & 0xF) + (b[2] >> 4) +
            (b[3] & 0xF) + (b[3] >> 4) +
            (b[4] >> 4)
        )
        checksum = ((b[4] & 0x0F) << 2) | last2
        if (nibble_sum & 0x3F) != checksum:
            return None

        device_id  = b[0]
        battery_ok = (b[1] >> 7) & 1
        tx_button  = (b[1] >> 6) & 1
        channel    = ((b[1] & 0x30) >> 4) + 1

        t16    = ((b[1] & 0x0F) << 12) | (b[2] << 4)
        temp_c = _sign16_top12(t16) * 0.1

        humidity = b[3] >> 1

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


__all__ = ["AuriolAHFL"]
