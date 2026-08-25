"""EMOS E6016 / E6018 wireless weather station."""
from __future__ import annotations
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


class EmosE6016(OOKPWMDecoder):
    """EMOS E6016 / E6018 wireless weather station.

    Modulation: OOK_PULSE_PWM
    short_us=280 (0-bit), long_us=796 (1-bit), reset_us=3000, n_bits=120
    The C decoder inverts the bitbuffer before parsing.
    Preamble: 0x55 0x5A 0x7C; checksum = sum(bytes[0..12]) mod 256 == bytes[13].

    Bit layout (120 bits, post-inversion, nibble notation PP PP PP II VK KK KK KK CT TT HH SS DF XX RR):
      bytes 0-2  : preamble 0x55 0x5A 0x7C
      byte  3    : house ID
      byte  4 b7-6 : variant (00=E6018, 10=E6016)
      bytes 4-7  : datetime (year 6b, month 4b, day 5b, hour 5b, min 6b, sec 6b) starting at bit 34
      bits 66-67 : channel (0-based, add 1)
      bits 68-79 : temperature (12-bit signed, /10 → °C)
      byte 10    : humidity %
      byte 11    : wind speed raw (* 0.295 → m/s, E6016 only)
      bits 96-99 : wind direction (* 22.5 → degrees, E6016 only)
      bits 100-103: flags (bit 101 = battery indicator)
      byte 13    : checksum
      byte 14    : repeat counter
    """

    name = "EMOS-E6016"
    short_us = 280.0
    long_us = 796.0
    reset_us = 3000.0
    n_bits = 120

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # The C decoder inverts the bitbuffer before all field checks.
        inv = [1 - b for b in bits]

        # Validate preamble
        if (bits_to_int(inv[0:8]) != 0x55
                or bits_to_int(inv[8:16]) != 0x5A
                or bits_to_int(inv[16:24]) != 0x7C):
            return None

        data = [bits_to_int(inv[i:i + 8]) for i in range(0, 120, 8)]  # 15 bytes

        # Checksum: sum of first 13 bytes mod 256 == byte 13
        if sum(data[:13]) & 0xFF != data[13]:
            return None

        device_id = data[3]
        variant = (data[4] >> 6) & 0x3  # top 2 bits of byte 4

        # Channel: 2-bit field starting at bit 66
        channel = bits_to_int(inv[66:68]) + 1

        # Temperature: 12-bit signed at bits 68-79
        temp_raw = bits_to_int(inv[68:80])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c = temp_raw / 10.0
        if not -60.0 <= temp_c <= 80.0:
            return None

        # Humidity: byte 10
        humidity = data[10]
        if not 0 <= humidity <= 100:
            return None

        # Flags nibble: bits 100-103; battery indicator at bit 101 (bit2 from MSB)
        battery_ok = not bool(inv[101])

        model_str = "EMOS-E6018" if variant == 0 else "EMOS-E6016"
        fields: dict = {
            "id": device_id,
            "channel": channel,
            "battery_ok": int(battery_ok),
            "temperature_C": round(temp_c, 1),
            "humidity": humidity,
        }

        # Wind and direction only present on E6016 variant
        if variant == 2:
            wind_ms = data[11] * 0.295
            wind_dir = bits_to_int(inv[96:100]) * 22.5
            fields["wind_avg_m_s"] = round(wind_ms, 2)
            fields["wind_dir_deg"] = round(wind_dir, 1)

        return DecodedPacket.from_fields(model_str, freq_hz, fields)


__all__ = ["EmosE6016"]
