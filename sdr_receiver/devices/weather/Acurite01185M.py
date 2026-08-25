"""Acurite 01185M Grill/Meat Thermometer (dual probe)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _reverse_byte(b: int) -> int:
    """Reverse all 8 bits in a byte (LSB-first → MSB-first)."""
    b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
    b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
    b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
    return b


def _add_with_carry(data: bytes) -> int:
    """Sum bytes, fold the carry back into the low byte (one pass)."""
    total = sum(data)
    return ((total & 0xFF) + (total >> 8)) & 0xFF


class Acurite01185M(OOKPWMDecoder):
    """Acurite 01185M Grill/Meat Thermometer (dual probe).

    r_device: OOK_PULSE_PWM, short=840, long=2070, reset=6000.
    Message: 56 bits (7 bytes), transmitted inverted + byte-reflected.
    Layout after invert + reflect:
      b[0]       = sensor ID
      b[1]       = battery(7), channel(3-0)  [channel values: 3, 6, 12, 15]
      b[2..3]    = probe 1 raw (meat); temp °F = (raw − 900) / 10
      b[4..5]    = probe 2 raw (ambient); temp °F = (raw − 900) / 10
      b[6]       = checksum: add-with-carry of b[0:6]
    Special raw values: 0x1B58 = probe unplugged, 0x00C8 = sensor fault.
    """
    name     = "Acurite-01185M"
    short_us = 840.0
    long_us  = 2070.0
    reset_us = 6000.0
    n_bits   = 56

    _UNPLUGGED = 0x1B58
    _FAULT     = 0x00C8

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        raw = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 56, 8))
        # Invert all bytes then reverse bit order within each byte
        b = bytes(_reverse_byte(x ^ 0xFF) for x in raw)
        # Reject all-zero false positives
        if not any(b):
            return None
        # Checksum: sum-with-carry of b[0:6] == b[6]
        if _add_with_carry(b[:6]) != b[6]:
            return None
        sensor_id  = b[0]
        battery_ok = not bool(b[1] >> 7)
        channel    = b[1] & 0x0F
        raw1 = (b[2] << 8) | b[3]
        raw2 = (b[4] << 8) | b[5]
        fields: dict = {
            "id":         sensor_id,
            "channel":    channel,
            "battery_ok": battery_ok,
        }
        for idx, raw_val, key_t, key_s in [
            (1, raw1, "temperature1_C", "probe1_status"),
            (2, raw2, "temperature2_C", "probe2_status"),
        ]:
            if raw_val == self._UNPLUGGED:
                fields[key_s] = "unplugged"
            elif raw_val == self._FAULT:
                fields[key_s] = "fault"
            elif 200 < raw_val < 7000:
                temp_f = (raw_val - 900) / 10.0
                temp_c = (temp_f - 32.0) * 5.0 / 9.0
                fields[key_t] = round(temp_c, 1)
                fields[key_s] = "ok"
            else:
                return None
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["Acurite01185M"]
