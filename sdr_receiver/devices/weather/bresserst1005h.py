"""Bresser Thermo-Hygro Sensor ST1005H / Explore Scientific OS0150 (OOK PPM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _add_nibbles
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BresserST1005H(OOKPPMDecoder):
    """Bresser Thermo-Hygro Sensor ST1005H / Explore Scientific OS0150 (OOK PPM).

    Protocol (38 bits, transmitted ≥ 3 times):
      [prefix:1=0] [id:8] [bat:1][btn:1][ch:2][temp_hi:4] [temp_lo:8]
      [hum:7][pad:1] [chk:6][pad:2]
    Temperature: signed 12-bit in tenths °C (bits [1:1] upper nibble + byte 2).
    Checksum: lower 6 bits of nibble-sum of the 4 message bytes.
    """
    name     = "Bresser-ST1005H"
    short_us = 2_500.0
    long_us  = 4_500.0
    reset_us = 10_000.0
    n_bits   = 38

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Bit 0 is a mandatory 0 prefix
        if bits[0] != 0:
            return None

        # Build 4 message bytes from bits 1..32
        msg = bytearray(
            bits_to_int(bits[1 + i * 8: 1 + i * 8 + 8]) for i in range(4)
        )
        msg[3] &= 0xFE   # clear the LSB of msg[3] (it belongs to the chk field)

        # 6-bit checksum occupying bits 32..37
        chk = bits_to_int(bits[32:38])

        nib_sum = _add_nibbles(bytes(msg))
        if nib_sum == 0 or chk != (nib_sum & 0x3F):
            return None

        device_id  = msg[0]
        battery_ok = not bool(msg[1] >> 7)
        button     = bool((msg[1] >> 6) & 0x01)
        channel    = ((msg[1] >> 4) & 0x03) + 1

        # Signed 12-bit temperature in bits 1:1 (upper nibble of msg[1]) + msg[2]
        temp_12 = ((msg[1] & 0x0F) << 8) | msg[2]
        if temp_12 >= 2048:
            temp_12 -= 4096
        temp_c = temp_12 * 0.1

        # 7-bit humidity from upper bits of msg[3] (LSB already cleared)
        humidity = msg[3] >> 1

        if channel >= 4 or humidity > 110 or not (-30.0 <= temp_c <= 160.0):
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "button":        button,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["BresserST1005H"]
