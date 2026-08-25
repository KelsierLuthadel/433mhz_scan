"""Nexus-TH legacy decoder (legacy standalone implementation).

Protocol: OOK_PWM, 36 bits, repeated 3–14×
Timing:   0 = ~500 µs pulse,  1 = ~1000 µs pulse  (gap ≈ inverse)
Frame:
  [id:8] [bat:1] [ch:2] [rsv:1] [temp:12] [hum:8] [crc:4]
  temp: signed 12-bit, value = °C × 10
  crc:  lower nibble of sum of all preceding nibbles

NOTE: This is the legacy standalone class (renamed to NexusTHLegacy to avoid
conflict with NexusTH in NexusTH.py).
"""
from __future__ import annotations

from ...dsp import Pulse, bits_to_int, pulses_to_bits_pwm
from ...packet import DecodedPacket

SHORT_US = 500.0
LONG_US  = 1_000.0
BITS     = 36


class NexusTHLegacy:
    name = "Nexus-TH"

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        # Drop sync / reset pulses; keep only bit-width ones
        data = [p for p in pulses if 80 <= p.pulse_us < 3_000]
        if len(data) < BITS:
            return None

        # Try up to 4 offsets in case of a preamble symbol
        for offset in range(min(5, len(data) - BITS + 1)):
            bits = pulses_to_bits_pwm(
                data[offset : offset + BITS],
                short_us=SHORT_US,
                long_us=LONG_US,
                tolerance=0.5,
            )
            if bits is None:
                continue
            pkt = self._parse(bits, freq_hz)
            if pkt is not None:
                return pkt
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        device_id = bits_to_int(bits[0:8])
        battery_ok = bool(bits[8])
        channel    = bits_to_int(bits[9:11]) + 1  # 0-indexed → 1-3

        temp_raw = bits_to_int(bits[12:24])
        if temp_raw >= 2048:          # sign-extend 12-bit
            temp_raw -= 4096
        temp_c = temp_raw / 10.0
        if not (-50.0 <= temp_c <= 80.0):
            return None

        humidity = bits_to_int(bits[24:32])
        if not (0 <= humidity <= 100):
            return None

        # CRC: lower nibble of the sum of nibbles 0-7
        nibble_sum = sum(bits_to_int(bits[i : i + 4]) for i in range(0, 32, 4))
        if (nibble_sum & 0xF) != bits_to_int(bits[32:36]):
            return None

        return DecodedPacket.from_fields(
            model=self.name,
            freq_hz=freq_hz,
            fields={
                "id":            device_id,
                "channel":       channel,
                "battery_ok":    battery_ok,
                "temperature_C": round(temp_c, 1),
                "humidity":      humidity,
            },
        )


__all__ = ["NexusTHLegacy"]
