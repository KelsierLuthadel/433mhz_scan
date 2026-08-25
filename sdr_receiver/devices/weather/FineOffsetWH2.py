"""Fine Offset WH2 / TFA 30.3157 / Conrad and compatible.

Protocol: OOK_PWM, 48 bits
Timing:   0 = ~500 µs pulse,  1 = ~1500 µs pulse
Frame (48 bits):
  [type:4] [id:12] [temp:12] [hum:8] [crc:8] [chk:4]
  temp: unsigned 12-bit, °C = (raw − 400) / 10
  crc:  sum of bytes 0-4, masked to 8 bits
"""
from __future__ import annotations

from ...dsp import Pulse, bits_to_int, checksum_sum, pulses_to_bits_pwm
from ...packet import DecodedPacket

SHORT_US = 500.0
LONG_US  = 1_500.0
BITS     = 48


class FineOffsetWH2:
    name = "Fine-Offset-WH2"

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        data = [p for p in pulses if 80 <= p.pulse_us < 4_000]
        if len(data) < BITS:
            return None

        for offset in range(min(5, len(data) - BITS + 1)):
            bits = pulses_to_bits_pwm(
                data[offset : offset + BITS],
                short_us=SHORT_US,
                long_us=LONG_US,
                tolerance=0.45,
            )
            if bits is None:
                continue
            pkt = self._parse(bits, freq_hz)
            if pkt is not None:
                return pkt
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Family nibble must be 0x5 (temp+hum sensor type)
        if bits_to_int(bits[0:4]) not in (0x5, 0xA):
            return None

        device_id = bits_to_int(bits[4:16])

        temp_raw = bits_to_int(bits[16:28])
        temp_c   = (temp_raw - 400) / 10.0
        if not (-60.0 <= temp_c <= 80.0):
            return None

        humidity = bits_to_int(bits[28:36])
        if not (0 <= humidity <= 100):
            return None

        raw_bytes = bytes(bits_to_int(bits[i : i + 8]) for i in range(0, 40, 8))
        crc_recv  = bits_to_int(bits[40:48])
        if checksum_sum(raw_bytes) != crc_recv:
            return None

        return DecodedPacket.from_fields(
            model=self.name,
            freq_hz=freq_hz,
            fields={
                "id":            device_id,
                "temperature_C": round(temp_c, 1),
                "humidity":      humidity,
            },
        )


__all__ = ["FineOffsetWH2"]
