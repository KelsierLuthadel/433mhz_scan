"""LaCrosse TX temperature/humidity sensor (OOK PWM, 44-bit)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseTX(OOKPWMDecoder):
    """LaCrosse TX temperature/humidity sensor (OOK PWM, 44-bit, 11 nibbles).

    NOTE: protocol uses short pulse = 1, long pulse = 0 (inverted vs base class).
    Message types: 0x00 = temperature, 0x0E = humidity.
    Checksum: sum of first 10 nibbles masked to 4 bits == nibble 10.
    """
    name     = "LaCrosse-TX"
    short_us = 550.0
    long_us  = 1_400.0
    reset_us = 8_000.0
    n_bits   = 44

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Invert: base gives short→0, long→1; this protocol is the reverse.
        bits = [1 - b for b in bits]

        nibbles = [bits_to_int(bits[i : i + 4]) for i in range(0, 44, 4)]

        if nibbles[0] != 0x0A:
            return None
        if (sum(nibbles[:10]) & 0xF) != nibbles[10]:
            return None

        msg_type  = nibbles[2]
        sensor_id = (nibbles[3] << 2) | (nibbles[4] >> 2)

        # Primary BCD value in nibbles 5-7 (tenths resolution)
        value = nibbles[5] * 100 + nibbles[6] * 10 + nibbles[7]

        if msg_type == 0x00:   # Temperature; subtract 50 °C
            temp_c = (value - 500) / 10.0
            if not -40.0 <= temp_c <= 60.0:
                return None
            return DecodedPacket.from_fields(self.name, freq_hz,
                {"id": sensor_id, "temperature_C": round(temp_c, 1)})

        if msg_type == 0x0E:   # Humidity (two BCD digits in nibbles 6-7)
            humidity = nibbles[6] * 10 + nibbles[7]
            if not 0 <= humidity <= 100:
                return None
            return DecodedPacket.from_fields(self.name, freq_hz,
                {"id": sensor_id, "humidity": humidity})

        return None


__all__ = ["LaCrosseTX"]
