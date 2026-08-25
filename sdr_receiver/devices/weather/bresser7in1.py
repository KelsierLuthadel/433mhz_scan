"""Bresser Weather Center 7-in-1 / Air Quality / CO2 / HCHO-VOC (FSK PCM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ._helpers import _lfsr_digest16, _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


# Sensor-type constants (byte 6 bits 7-4, read BEFORE XOR whitening)
_7IN1_TYPE_WEATHER   = 1    # standard 7-in-1 weather station
_7IN1_TYPE_AIR_PM    = 8    # air quality PM2.5 / PM10 (model 7009970)
_7IN1_TYPE_CO2       = 10   # CO2 sensor (model 7009977)
_7IN1_TYPE_HCHO_VOC  = 11   # HCHO / VOC sensor (model 7009978)
_7IN1_TYPE_WEATHER3  = 12   # 3-in-1 indoor (no wind / light)
_7IN1_TYPE_WEATHER8  = 13   # 8-in-1 station (+ globe temperature)


class Bresser7in1(FSKPCMDecoder):
    """Bresser Weather Center 7-in-1 / Air Quality / CO2 / HCHO-VOC (FSK PCM).

    Preamble: AA AA AA 2D D4  (5 bytes)
    Payload:  25 bytes, XOR-whitened with 0xAA.
    Integrity: LFSR-16 keyed digest with key 0xBA95 XOR'd against 0x6DF1.
    """
    name     = "Bresser-7in1"
    bit_rate = 1_000_000.0 / 124.0
    n_bits   = 440

    _PREAMBLE = bytes([0xAA, 0xAA, 0xAA, 0x2D, 0xD4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        start = _find_preamble(bits, self._PREAMBLE)
        if start < 0:
            return None

        raw = _extract_bytes(bits, start, 25)
        if raw is None:
            return None

        # Sanity pre-check on the whitened byte 21
        if raw[21] == 0x00:
            return None

        # Sensor type / channel extracted BEFORE XOR de-whitening
        s_type   = raw[6] >> 4
        nstartup = bool((raw[6] & 0x08) >> 3)
        chan     = raw[6] & 0x07

        # Remove XOR whitening (0xAA per byte)
        msg = bytes(b ^ 0xAA for b in raw)

        # LFSR-16 integrity check: (chk ^ digest) must equal 0x6DF1
        chk    = (msg[0] << 8) | msg[1]
        digest = _lfsr_digest16(msg[2:25], 0x8810, 0xBA95)
        if (chk ^ digest) != 0x6DF1:
            return None

        dev_id     = (msg[2] << 8) | msg[3]
        flags      = msg[15] & 0x0F
        battery_ok = not ((flags & 0x06) == 0x06)

        base: dict = {
            "id":         dev_id,
            "channel":    chan,
            "battery_ok": battery_ok,
        }
        if nstartup:
            base["startup"] = 1

        if s_type in (_7IN1_TYPE_WEATHER, _7IN1_TYPE_WEATHER3, _7IN1_TYPE_WEATHER8):
            return self._parse_weather(msg, freq_hz, base, s_type)
        if s_type == _7IN1_TYPE_AIR_PM:
            return self._parse_air_pm(msg, freq_hz, base)
        if s_type == _7IN1_TYPE_CO2:
            return self._parse_co2(msg, freq_hz, base)
        if s_type == _7IN1_TYPE_HCHO_VOC:
            return self._parse_hcho_voc(msg, freq_hz, base)
        return None   # unsupported sensor type

    # ------------------------------------------------------------------
    def _parse_weather(self, msg: bytes, freq_hz: float,
                       base: dict, s_type: int) -> DecodedPacket | None:
        # Wind: available except for type 12 (3-in-1 indoor, no anemometer)
        wind_light_ok = (s_type != _7IN1_TYPE_WEATHER3)

        # Wind direction (BCD, degrees)
        wdir = ((msg[4] >> 4) * 100
                + (msg[4] & 0x0F) * 10
                + (msg[5] >> 4))

        # Wind gust (BCD, 1/10 m/s)
        wgst_raw = ((msg[7] >> 4) * 100
                    + (msg[7] & 0x0F) * 10
                    + (msg[8] >> 4))

        # Wind average (BCD, 1/10 m/s)
        wavg_raw = ((msg[8] & 0x0F) * 100
                    + (msg[9] >> 4) * 10
                    + (msg[9] & 0x0F))

        # Rain (BCD, 1/10 mm cumulative)
        rain_raw = ((msg[10] >> 4) * 100_000
                    + (msg[10] & 0x0F) * 10_000
                    + (msg[11] >> 4) * 1_000
                    + (msg[11] & 0x0F) * 100
                    + (msg[12] >> 4) * 10
                    + (msg[12] & 0x0F))

        # Temperature (BCD, 1/10 °C; raw > 600 means negative via offset of 1000)
        temp_raw = ((msg[14] >> 4) * 100
                    + (msg[14] & 0x0F) * 10
                    + (msg[15] >> 4))
        temp_c = temp_raw * 0.1
        if temp_raw > 600:
            temp_c = (temp_raw - 1000) * 0.1

        # Humidity (BCD)
        humidity = (msg[16] >> 4) * 10 + (msg[16] & 0x0F)

        # Light / UV (BCD, lux and 1/10 UV index)
        lght_raw = ((msg[17] >> 4) * 100_000
                    + (msg[17] & 0x0F) * 10_000
                    + (msg[18] >> 4) * 1_000
                    + (msg[18] & 0x0F) * 100
                    + (msg[19] >> 4) * 10
                    + (msg[19] & 0x0F))
        uv_raw = ((msg[20] >> 4) * 100
                  + (msg[20] & 0x0F) * 10
                  + (msg[21] >> 4))

        fields = dict(base)
        fields["temperature_C"] = round(temp_c, 1)
        fields["humidity"]      = humidity
        fields["rain_mm"]       = round(rain_raw * 0.1, 1)

        if wind_light_ok:
            fields["wind_max_m_s"] = round(wgst_raw * 0.1, 1)
            fields["wind_avg_m_s"] = round(wavg_raw * 0.1, 1)
            fields["wind_dir_deg"] = wdir
            fields["light_lux"]    = float(lght_raw)
            fields["uvi"]          = round(uv_raw * 0.1, 1)

        # Globe temperature available on WEATHER8 variant
        if s_type == _7IN1_TYPE_WEATHER8 and (msg[23] >> 4) < 10:
            tglobe = ((msg[22] >> 4) * 10
                      + (msg[22] & 0x0F)
                      + (msg[23] >> 4) * 0.1)
            fields["temperature_1_C"] = round(tglobe, 1)

        return DecodedPacket.from_fields(self.name, freq_hz, fields)

    # ------------------------------------------------------------------
    def _parse_air_pm(self, msg: bytes, freq_hz: float,
                      base: dict) -> DecodedPacket | None:
        pm25_init = (msg[10] & 0x0F) == 0x0F
        pm10_init = (msg[12] & 0x0F) == 0x0F
        pm_2_5 = ((msg[10] & 0x0F) * 1000
                  + (msg[11] >> 4) * 100
                  + (msg[11] & 0x0F) * 10
                  + (msg[12] >> 4))
        pm_10  = ((msg[12] & 0x0F) * 1000
                  + (msg[13] >> 4) * 100
                  + (msg[13] & 0x0F) * 10
                  + (msg[14] >> 4))
        fields = dict(base)
        if not pm25_init:
            fields["pm2_5_ug_m3"]  = pm_2_5
        if not pm10_init:
            fields["pm10_0_ug_m3"] = pm_10
        return DecodedPacket.from_fields("Bresser-AirQuality", freq_hz, fields)

    # ------------------------------------------------------------------
    def _parse_co2(self, msg: bytes, freq_hz: float,
                   base: dict) -> DecodedPacket | None:
        co2_raw  = (((msg[4] & 0xF0) >> 4) * 1000
                    + (msg[4] & 0x0F) * 100
                    + ((msg[5] & 0xF0) >> 4) * 10
                    + (msg[5] & 0x0F))
        co2_init = (msg[5] & 0x0F) == 0x0F
        fields   = dict(base)
        if not co2_init:
            fields["co2_ppm"] = co2_raw
        return DecodedPacket.from_fields("Bresser-CO2", freq_hz, fields)

    # ------------------------------------------------------------------
    def _parse_hcho_voc(self, msg: bytes, freq_hz: float,
                        base: dict) -> DecodedPacket | None:
        hcho_raw  = (((msg[4] & 0xF0) >> 4) * 1000
                     + (msg[4] & 0x0F) * 100
                     + ((msg[5] & 0xF0) >> 4) * 10
                     + (msg[5] & 0x0F))
        hcho_init = (msg[5] & 0x0F) == 0x0F
        voc       = msg[22] & 0x0F
        voc_init  = voc == 0x0F
        fields    = dict(base)
        if not hcho_init:
            fields["hcho_ppb"] = hcho_raw
        if not voc_init:
            fields["voc_level"] = voc
        return DecodedPacket.from_fields("Bresser-HCHOVOC", freq_hz, fields)


__all__ = ["Bresser7in1"]
