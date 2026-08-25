"""Acurite 609TXC and similar temperature/humidity sensors.

Protocol: OOK_PWM, 56 bits
Timing:   0 = ~200 µs pulse,  1 = ~400 µs pulse  (gap ≈ 200 µs)
Frame (56 bits):
  [preamble:8=0xFF] [id:8] [bat:1] [ch:2] [rsv:5] [temp:11] [hum:8] [crc:8] [sum:8]
  temp: unsigned 11-bit, °C = (raw − 100) / 10
"""
from __future__ import annotations

from ...dsp import Pulse, bits_to_int, checksum_sum, pulses_to_bits_pwm
from ...packet import DecodedPacket

SHORT_US = 200.0
LONG_US  = 400.0
BITS     = 56


class Acurite609:
    name = "Acurite-609TXC"

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        data = [p for p in pulses if 60 <= p.pulse_us < 3_000]
        if len(data) < BITS:
            return None

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
        # Preamble byte should be 0xFF
        if bits_to_int(bits[0:8]) != 0xFF:
            return None

        device_id  = bits_to_int(bits[8:16])
        battery_ok = bool(bits[16])
        channel    = bits_to_int(bits[17:19]) + 1

        temp_raw = bits_to_int(bits[24:35])
        temp_c   = (temp_raw - 1000) / 10.0
        if not (-40.0 <= temp_c <= 70.0):
            return None

        humidity = bits_to_int(bits[35:43])
        if not (0 <= humidity <= 100):
            return None

        # Checksum: sum of bytes 0-5 == byte 6
        raw_bytes = bytes(bits_to_int(bits[i : i + 8]) for i in range(0, 48, 8))
        crc_recv  = bits_to_int(bits[48:56])
        if checksum_sum(raw_bytes) != crc_recv:
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


__all__ = ["Acurite609"]
