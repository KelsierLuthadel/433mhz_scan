"""Bresser Weather Center 5-in-1 / Professional Rain Gauge (FSK PCM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Bresser5in1(FSKPCMDecoder):
    """Bresser Weather Center 5-in-1 / Professional Rain Gauge (FSK PCM).

    Preamble: AA AA AA 2D D4  (5 bytes)
    Payload:  26 bytes  first 13 bytes repeated inverted in bytes 13–25.
    No separate CRC; integrity via per-byte parity (XOR == 0xFF).
    """
    name     = "Bresser-5in1"
    bit_rate = 1_000_000.0 / 124.0   # ~8065 bps
    n_bits   = 440                    # enough to hold preamble + payload

    _PREAMBLE = bytes([0xAA, 0xAA, 0xAA, 0x2D, 0xD4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        start = _find_preamble(bits, self._PREAMBLE)
        if start < 0:
            return None

        msg = _extract_bytes(bits, start, 26)
        if msg is None:
            return None

        # Parity: each of the first 13 bytes must be the bitwise inverse of
        # the corresponding byte in the second 13 bytes.
        for i in range(13):
            if (msg[i] ^ msg[i + 13]) != 0xFF:
                return None

        sensor_id   = msg[14]
        sensor_type = msg[15] & 0x7F
        battery_ok  = not bool(msg[25] & 0x80)

        # Temperature  BCD, tenths °C; sign flag in low nibble of msg[25]
        temp_ok  = (msg[20] & 0x0F) <= 9
        temp_raw = ((msg[20] & 0x0F)
                    + ((msg[20] & 0xF0) >> 4) * 10
                    + (msg[21] & 0x0F) * 100)
        if msg[25] & 0x0F:
            temp_raw = -temp_raw
        temp_c = temp_raw * 0.1

        # Humidity  BCD
        hum_ok   = (msg[22] & 0x0F) <= 9
        humidity = (msg[22] & 0x0F) + ((msg[22] & 0xF0) >> 4) * 10

        # Wind direction: upper nibble of msg[17], in 22.5° steps
        wind_dir_deg = ((msg[17] & 0xF0) >> 4) * 22.5

        # Wind gust: binary 12-bit value (lower nibble msg[17] | msg[16]), 1/10 m/s
        gust_raw  = ((msg[17] & 0x0F) << 8) | msg[16]
        wind_gust = gust_raw * 0.1

        # Wind average  BCD, 1/10 m/s
        wind_raw = ((msg[18] & 0x0F)
                    + ((msg[18] & 0xF0) >> 4) * 10
                    + (msg[19] & 0x0F) * 100)
        wind_avg = wind_raw * 0.1

        # Rain  BCD, 1/10 mm
        rain_raw = ((msg[23] & 0x0F)
                    + ((msg[23] & 0xF0) >> 4) * 10
                    + (msg[24] & 0x0F) * 100
                    + ((msg[24] & 0xF0) >> 4) * 1000)
        rain_mm = rain_raw * 0.1

        # Professional rain gauge uses a 2.5× multiplier and different model name
        if 0x39 <= sensor_type <= 0x3B:
            rain_mm *= 2.5
            model = "Bresser-ProRainGauge"
        else:
            model = self.name

        fields: dict = {
            "id":         sensor_id,
            "battery_ok": battery_ok,
        }
        if temp_ok:
            fields["temperature_C"] = round(temp_c, 1)
        if hum_ok:
            fields["humidity"] = humidity
        if model == self.name:
            fields["wind_max_m_s"] = round(wind_gust, 1)
            fields["wind_avg_m_s"] = round(wind_avg, 1)
            fields["wind_dir_deg"] = wind_dir_deg
        fields["rain_mm"] = round(rain_mm, 1)

        return DecodedPacket.from_fields(model, freq_hz, fields)


__all__ = ["Bresser5in1"]
