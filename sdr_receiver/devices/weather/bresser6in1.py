"""Bresser Weather Center 6-in-1 / 7-in-1 indoor / soil / Froggit WH6000 (FSK PCM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ._helpers import _lfsr_digest16, _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


# Sensor-type constants (embedded in byte 6, bits 7-4)
_6IN1_TYPE_WEATHER    = 1   # standard weather station
_6IN1_TYPE_THERMO     = 2   # thermo/hygro only (no wind / UV)
_6IN1_TYPE_POOL       = 3   # pool thermometer
_6IN1_TYPE_SOIL       = 4   # soil moisture + temperature
# Moisture code → percentage lookup (code 1..16 maps to approximate % values)
_SOIL_MOISTURE_TABLE  = [0, 7, 13, 20, 27, 33, 40, 47, 53, 60, 67, 73, 80, 87, 93, 99]


class Bresser6in1(FSKPCMDecoder):
    """Bresser Weather Center 6-in-1 / 7-in-1 indoor / soil / Froggit WH6000.

    Preamble: AA AA 2D D4  (4 bytes)
    Payload:  18 bytes
    Integrity: LFSR-16 digest (bytes 2–16) + additive sum of bytes 2–17 == 0xFF.
    """
    name     = "Bresser-6in1"
    bit_rate = 1_000_000.0 / 124.0
    n_bits   = 440

    _PREAMBLE = bytes([0xAA, 0xAA, 0x2D, 0xD4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        start = _find_preamble(bits, self._PREAMBLE)
        if start < 0:
            return None

        msg = _extract_bytes(bits, start, 18)
        if msg is None:
            return None

        # LFSR-16 digest over bytes 2–16 (15 bytes)
        digest = _lfsr_digest16(msg[2:17], 0x8810, 0x5412)
        if ((msg[0] << 8) | msg[1]) != digest:
            return None

        # Additive checksum: sum of bytes 2–17 (16 bytes) & 0xFF == 0xFF
        if sum(msg[2:18]) & 0xFF != 0xFF:
            return None

        s_type   = msg[6] >> 4
        nstartup = bool((msg[6] & 0x08) >> 3)
        chan     = msg[6] & 0x07
        dev_id   = (msg[2] << 24) | (msg[3] << 16) | (msg[4] << 8) | msg[5]

        # Battery: bit 1 of byte 13 (0 = OK, 1 = low)
        battery_ok = not bool(msg[13] & 0x02)

        base: dict = {
            "id":         f"{dev_id:08x}",
            "channel":    chan,
            "battery_ok": battery_ok,
        }
        if nstartup:
            base["startup"] = 1

        if s_type == _6IN1_TYPE_SOIL:
            return self._parse_soil(msg, freq_hz, base)
        if s_type in (_6IN1_TYPE_WEATHER, _6IN1_TYPE_THERMO, _6IN1_TYPE_POOL):
            return self._parse_weather(msg, freq_hz, base, s_type)
        # Unknown sensor type  return minimal packet with raw bytes for analysis
        return DecodedPacket.from_fields(self.name, freq_hz,
                                         {**base, "raw": msg.hex()})

    # ------------------------------------------------------------------
    def _parse_weather(self, msg: bytes, freq_hz: float,
                       base: dict, s_type: int) -> DecodedPacket | None:
        # Temperature  bytes 12–13 stored inverted, BCD, sign in bit 3 of t13
        t12 = msg[12] ^ 0xFF
        t13 = msg[13] ^ 0xFF
        # BCD validity: each nibble must be ≤ 9
        if (t12 & 0xF0) > 0x90 or (t12 & 0x0F) > 9:
            return None
        temp_raw = (t12 >> 4) * 100 + (t12 & 0x0F) * 10 + (t13 >> 4)
        negative = bool(t13 & 0x08)
        temp_c   = (-temp_raw if negative else temp_raw) * 0.1

        # Humidity  byte 14 inverted, BCD
        h14      = msg[14] ^ 0xFF
        humidity = (h14 >> 4) * 10 + (h14 & 0x0F)

        if not (-40.0 <= temp_c <= 80.0) or not (0 <= humidity <= 100):
            return None

        fields = dict(base)
        fields["temperature_C"] = round(temp_c, 1)
        fields["humidity"]      = humidity

        if s_type == _6IN1_TYPE_WEATHER:
            # Wind bytes 7–9 stored inverted
            w7 = msg[7] ^ 0xFF
            w8 = msg[8] ^ 0xFF
            w9 = msg[9] ^ 0xFF

            # Wind gust (BCD, 1/10 m/s): hundreds/tens/ones in w7, tenth in w8 upper nibble
            gust_raw  = (w7 >> 4) * 100 + (w7 & 0x0F) * 10 + (w8 >> 4)
            # Wind average (BCD, 1/10 m/s): hundreds/tens/ones in w9, tenth in w8 lower nibble
            avg_raw   = (w9 >> 4) * 100 + (w9 & 0x0F) * 10 + (w8 & 0x0F)
            # Wind direction (BCD, degrees 0–359)
            wind_dir  = (msg[10] >> 4) * 100 + (msg[10] & 0x0F) * 10 + (msg[11] >> 4)

            fields["wind_max_m_s"] = round(gust_raw * 0.1, 1)
            fields["wind_avg_m_s"] = round(avg_raw  * 0.1, 1)
            fields["wind_dir_deg"] = wind_dir

            # Rain counter (bytes 12–14 inverted, BCD, 1/10 mm cumulative)
            rain_raw = ((msg[12] ^ 0xFF) >> 4) * 100_000 \
                     + ((msg[12] ^ 0xFF) & 0x0F) * 10_000 \
                     + ((msg[13] ^ 0xFF) >> 4) * 1_000 \
                     + ((msg[13] ^ 0xFF) & 0x0F) * 100 \
                     + ((msg[14] ^ 0xFF) >> 4) * 10 \
                     + ((msg[14] ^ 0xFF) & 0x0F)
            fields["rain_mm"] = round(rain_raw * 0.1, 1)

            # UV index (bytes 15–16 inverted, BCD, 1/10 index)
            u15 = msg[15] ^ 0xFF
            u16 = msg[16] ^ 0xFF
            uv_raw = (u15 >> 4) * 100 + (u15 & 0x0F) * 10 + (u16 >> 4)
            fields["uvi"] = round(uv_raw * 0.1, 1)

        return DecodedPacket.from_fields(self.name, freq_hz, fields)

    # ------------------------------------------------------------------
    def _parse_soil(self, msg: bytes, freq_hz: float,
                    base: dict) -> DecodedPacket | None:
        # Temperature  bytes 12–13 inverted (same layout as weather)
        t12 = msg[12] ^ 0xFF
        t13 = msg[13] ^ 0xFF
        temp_raw = (t12 >> 4) * 100 + (t12 & 0x0F) * 10 + (t13 >> 4)
        negative = bool(t13 & 0x08)
        temp_c   = (-temp_raw if negative else temp_raw) * 0.1

        # Soil moisture code in byte 14 (inverted), range 1–16
        h14           = msg[14] ^ 0xFF
        moisture_code = (h14 >> 4) * 10 + (h14 & 0x0F)

        fields = dict(base)
        fields["temperature_C"] = round(temp_c, 1)
        if 1 <= moisture_code <= 16:
            fields["moisture"] = _SOIL_MOISTURE_TABLE[moisture_code - 1]

        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["Bresser6in1"]
