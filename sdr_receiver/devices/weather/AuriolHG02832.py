"""Auriol HG02832 / HG05124A-DCF / Rubicson 48957 temperature/humidity sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ._helpers import _sign16_top12
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class AuriolHG02832(OOKPWMDecoder):
    """Auriol HG02832 / HG05124A-DCF / Rubicson 48957 temperature/humidity sensor."""
    name     = "Auriol-HG02832"
    short_us = 252.0
    long_us  = 612.0
    reset_us = 62_990.0
    n_bits   = 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 40:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 40, 8)]

        # CRC-8: input is the XOR of the first four bytes
        d0  = b[0] ^ b[1] ^ b[2] ^ b[3]
        chk = crc8(bytes([d0]), poly=0x31, init=0x53)
        if chk != b[4]:
            return None

        device_id  = b[0]
        humidity   = b[1]
        battery_ok = (b[2] >> 7) & 1
        tx_button  = (b[2] >> 6) & 1
        channel    = ((b[2] >> 4) & 0x03) + 1

        t16    = ((b[2] & 0x0F) << 12) | (b[3] << 4)
        temp_c = _sign16_top12(t16) * 0.1

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


__all__ = ["AuriolHG02832"]
