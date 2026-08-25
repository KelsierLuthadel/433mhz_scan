"""Acurite 00275rm Indoor Temperature + Humidity Sensor with probe."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Acurite00275RM(OOKPWMDecoder):
    """Acurite 00275rm Indoor Temperature + Humidity Sensor with probe.

    r_device: OOK_PULSE_PWM, short=232, long=420, reset=708.
    Message: 88 bits (11 bytes).
      b[0..2]    = ID (24 bits)
      b[3]       = battery(7), model ID (6-0)
      b[4]       = temp high nibble (7-4), probe type (3-0)
      b[5]       = temp low byte
      b[6]       = humidity flags (7-5), humidity high (4-0)
      b[7]       = humidity low (7-6), probe data (5-0)
      b[8]       = probe data continued
      b[9..10]   = CRC-16 (poly=0x00B2, init=0x00D0, LSB-first) over b[0:9]
    """
    name     = "Acurite-00275rm"
    short_us = 232.0
    long_us  = 420.0
    reset_us = 708.0
    n_bits   = 88

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 88, 8))
        # CRC-16 (LSB-first, ref_in=True ref_out=True) over first 9 bytes;
        # bytes 9-10 hold the CRC (little-endian).
        crc_recv = b[9] | (b[10] << 8)
        crc_calc = crc16(b[:9], poly=0x00B2, init=0x00D0, ref_in=True, ref_out=True)
        if crc_calc != crc_recv:
            return None
        sensor_id  = (b[0] << 16) | (b[1] << 8) | b[2]
        battery_ok = not bool(b[3] >> 7)
        temp_raw   = ((b[4] & 0xF0) << 4) | b[5]   # 12-bit unsigned
        temp_c     = (temp_raw - 1000) / 10.0
        humidity   = ((b[6] & 0x1F) << 2) | (b[7] >> 6)
        probe_type = b[4] & 0x0F
        if not -40.0 <= temp_c <= 70.0:
            return None
        fields = {
            "id":            sensor_id,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
            "probe_type":    probe_type,
        }
        # Probe-specific data
        if probe_type == 1:
            # Water / leak probe
            fields["water_detect"] = bool(b[7] & 0x20)
        elif probe_type in (2, 3):
            # Soil / spot temp probe
            probe_raw  = ((b[7] & 0x3F) << 6) | (b[8] >> 2)
            probe_temp = (probe_raw - 1000) / 10.0
            fields["probe_temperature_C"] = round(probe_temp, 1)
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["Acurite00275RM"]
