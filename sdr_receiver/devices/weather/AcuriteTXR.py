"""Acurite 592TXR tower + 5n1 weather station + 6045M lightning + 899 rain."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int, crc8, crc16, checksum_sum, pulses_to_bits_pwm
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _even_parity8(b: int) -> bool:
    """Return True if byte has even parity."""
    b ^= b >> 4
    b ^= b >> 2
    b ^= b >> 1
    return (b & 1) == 0


# Wind direction lookup table (index 0–15) from rtl_433 acurite 5n1 decoder
_5N1_WIND_DIR_NAME = [
    "NW", "WSW", "WNW", "W", "NNW", "SW", "N", "SSW",
    "ENE", "SE", "E", "ESE", "NE", "SSE", "NNE", "S",
]
_5N1_WIND_DIR_DEG = [
    315.0, 247.5, 292.5, 270.0, 337.5, 225.0, 0.0, 202.5,
    67.5, 135.0, 90.0, 112.5, 45.0, 157.5, 22.5, 180.0,
]


class AcuriteTXR(RawDecoder):
    """Acurite 592TXR tower + 5n1 weather station + 6045M lightning + 899 rain.

    r_device: OOK_PULSE_PWM, short=220, long=408, gap=500, reset=4000.
    Messages are 7–10 bytes (56–80 bits) depending on message type:
      0x04 → 7 bytes   tower (temp only)
      0x38 → 8 bytes   5n1 temp + humidity
      0x31 → 8 bytes   5n1 wind + rain
      0x30 → 8 bytes   899 rain gauge
      0x2F → 9 bytes   6045M lightning
      0x25/0x26/0x27 → 8–10 bytes  Atlas
    Checksum: sum(b[0:-1]) & 0xFF == b[-1].
    Even parity on b[2:-2].
    """
    name     = "Acurite-Tower"
    short_us = 220.0
    long_us  = 408.0
    reset_us = 4000.0

    _CHANNEL_MAP: dict[int, str] = {0b11: 'A', 0b10: 'B', 0b00: 'C'}
    _VALID_LENGTHS: tuple[int, ...] = (56, 64, 72, 80)

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        data = [p for p in pulses if 50 < p.pulse_us < self.reset_us]
        for nbits in self._VALID_LENGTHS:
            if len(data) < nbits:
                continue
            for off in range(min(5, len(data) - nbits + 1)):
                bits = pulses_to_bits_pwm(
                    data[off:off + nbits], self.short_us, self.long_us, tolerance=0.45
                )
                if bits is None:
                    continue
                result = self._parse(bits, freq_hz)
                if result is not None:
                    return result
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        nbytes = len(bits) // 8
        if nbytes < 7:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, nbytes * 8, 8))

        # Checksum: sum of all bytes except last == last byte
        if (sum(b[:-1]) & 0xFF) != b[-1]:
            return None

        # Even parity on data bytes b[2:-2]
        for i in range(2, nbytes - 2):
            if not _even_parity8(b[i]):
                return None

        ch_raw     = (b[0] >> 6) & 0x03
        channel    = self._CHANNEL_MAP.get(ch_raw, '?')
        sensor_id  = ((b[0] & 0x3F) << 8) | b[1]
        battery_ok = bool((b[2] >> 6) & 1)
        msg_type   = b[2] & 0x3F

        base = {
            "id":           sensor_id,
            "channel":      channel,
            "battery_ok":   battery_ok,
            "message_type": f"0x{msg_type:02X}",
        }

        if msg_type == 0x04 and nbytes == 7:
            # Tower sensor  temperature only
            temp_raw = ((b[4] & 0x7F) << 7) | (b[5] & 0x7F)
            temp_c   = (temp_raw - 1000) / 10.0
            if not -40.0 <= temp_c <= 70.0:
                return None
            base.update(model="Acurite-Tower", temperature_C=round(temp_c, 1))

        elif msg_type == 0x38 and nbytes == 8:
            # 5n1  temperature + humidity
            temp_raw = ((b[4] & 0x0F) << 7) | (b[5] & 0x7F)
            temp_f   = (temp_raw - 400) / 10.0
            temp_c   = (temp_f - 32.0) * 5.0 / 9.0
            humidity = b[6] & 0x7F
            if not 0 <= humidity <= 100:
                return None
            base.update(model="Acurite-5n1", temperature_C=round(temp_c, 1),
                        humidity=humidity)

        elif msg_type == 0x31 and nbytes == 8:
            # 5n1  wind speed, direction + rain
            wind_raw   = ((b[3] & 0x1F) << 3) | ((b[4] & 0x70) >> 4)
            wind_mph   = wind_raw * 0.5
            dir_idx    = b[4] & 0x0F
            rain_raw   = ((b[5] & 0x7F) << 7) | (b[6] & 0x7F)
            rain_in    = rain_raw * 0.01
            base.update(
                model="Acurite-5n1",
                wind_speed_mph=round(wind_mph, 1),
                wind_dir=_5N1_WIND_DIR_NAME[dir_idx],
                wind_dir_deg=_5N1_WIND_DIR_DEG[dir_idx],
                rain_in=round(rain_in, 2),
            )

        elif msg_type == 0x30 and nbytes == 8:
            # 899 rain gauge
            rain_raw = ((b[5] & 0x7F) << 7) | (b[6] & 0x7F)
            rain_mm  = rain_raw * 0.254
            base.update(model="Acurite-899", rain_mm=round(rain_mm, 2))

        elif msg_type == 0x2F and nbytes == 9:
            # 6045M lightning detector
            temp_raw   = ((b[4] & 0x1F) << 7) | (b[5] & 0x7F)
            temp_f     = (temp_raw - 1480) / 10.0
            temp_c     = (temp_f - 32.0) * 5.0 / 9.0
            strikes    = b[6] & 0xFF
            distance   = b[7] & 0x1F
            base.update(
                model="Acurite-6045M",
                temperature_C=round(temp_c, 1),
                lightning_strikes=strikes,
                lightning_distance_km=distance,
            )

        else:
            # Unknown / Atlas / Optimus  return raw bytes for inspection
            base["raw_bytes"] = b.hex()

        return DecodedPacket.from_fields(self.name, freq_hz, base)


__all__ = ["AcuriteTXR"]
