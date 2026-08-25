"""LaCrosse WS-2310 / WS-3600 weather station (OOK PWM, 52 bits)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseWS2310(OOKPWMDecoder):
    """LaCrosse WS-2310 / WS-3600 weather station (OOK PWM, 52 bits, 13 nibbles).

    Message types: 0=temperature, 1=humidity, 2=rain, 3=wind, 7=gust.
    Validation: inverse check on nibbles 7-8 vs 10-11, nibble-sum checksum.
    """
    name     = "LaCrosse-WS2310"
    short_us = 368.0
    long_us  = 1_464.0
    reset_us = 8_000.0
    n_bits   = 52

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 52:
            return None
        nibbles = [bits_to_int(bits[i : i + 4]) for i in range(0, 52, 4)]

        ws_id     = (nibbles[0] << 4) | nibbles[1]
        msg_type  = ((nibbles[2] >> 1) & 0x4) | (nibbles[2] & 0x3)
        sensor_id = (nibbles[3] << 4) | nibbles[4]

        v7, v8, v9   = nibbles[7], nibbles[8], nibbles[9]
        inv10, inv11 = nibbles[10], nibbles[11]
        checksum     = nibbles[12]

        # Inverse checks
        if v7 != (inv10 ^ 0xF) or v8 != (inv11 ^ 0xF):
            return None

        # Nibble-sum checksum
        if (sum(nibbles[:12]) & 0xF) != checksum:
            return None

        model = "LaCrosse-WS3600" if ws_id == 0x6 else "LaCrosse-WS2310"
        fields: dict = {"id": sensor_id}

        if msg_type == 0:
            bcd   = v7 * 100 + v8 * 10 + v9
            temp_c = (bcd - 400) / 10.0 if ws_id == 0x6 else (bcd - 300) / 10.0
            if not -40.0 <= temp_c <= 80.0:
                return None
            fields["temperature_C"] = round(temp_c, 1)

        elif msg_type == 1:
            if v7 == 0xA and v8 == 0xA:
                return None
            fields["humidity"] = v7 * 10 + v8

        elif msg_type == 2:
            fields["rain_mm"] = round(0.518 * (v7 * 256 + v8 * 16 + v9), 2)

        elif msg_type in (3, 7):
            if v7 == 0xF and v8 == 0xE:
                return None
            wind_spd = (v7 * 16 + v8) * 0.1
            wind_dir = v9 * 22.5
            if msg_type == 3:
                fields.update({"wind_avg_m_s": round(wind_spd, 1), "wind_dir_deg": wind_dir})
            else:
                fields.update({"wind_max_m_s": round(wind_spd, 1), "wind_dir_deg": wind_dir})

        else:
            return None

        return DecodedPacket.from_fields(model, freq_hz, fields)


__all__ = ["LaCrosseWS2310"]
