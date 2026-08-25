"""Baldr / Thermor E0666TH thermo-hygrometer."""
from __future__ import annotations
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


class BaldrTherm(OOKPPMDecoder):
    """Baldr / Thermor E0666TH thermo-hygrometer.

    Modulation: OOK_PULSE_PPM
    short_us=1000 (gap=0), long_us=2000 (gap=1), reset_us=5000, n_bits=64

    Bit layout (64 bits, 16 nibbles  II FT TT fH H0 00 0S JJ):
      byte 0 [II] : device ID
      byte 1 upper nibble [F] : bit8=battery_ok, bits10-11=channel(+1)
      byte 1 lower + byte 2 [TTT] : 12-bit signed temperature (/10 → °C)
      byte 3 upper nibble [f] : fixed 0xF (validation)
      byte 3 lower + byte 4 upper [HH] : humidity (BCD tens + units)
      byte 4 lower + byte 5 [000] : zeros (validation)
      byte 6 upper [0] : zero
      byte 6 lower [S] : startup nibble
      byte 7 [JJ] : ID confirmation
    """

    name = "Baldr-Therm"
    short_us = 1000.0
    long_us = 2000.0
    reset_us = 5000.0
    n_bits = 64

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        device_id = bits_to_int(bits[0:8])

        # Byte 1 upper nibble: battery at bit7 (bits[8]), channel at bits5-4 (bits[10:12])
        battery_ok = bool(bits[8])
        channel = bits_to_int(bits[10:12]) + 1

        # Temperature: 12-bit signed from byte1-lower + byte2 (bits 12-23)
        temp_raw = bits_to_int(bits[12:24])
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c = temp_raw / 10.0
        if not -50.0 <= temp_c <= 80.0:
            return None

        # Fixed 0xF at byte3 upper nibble (bits 24-27)
        if bits_to_int(bits[24:28]) != 0xF:
            return None

        # Humidity: BCD at byte3-lower (tens, bits 28-31) + byte4-upper (units, bits 32-35)
        hum_tens = bits_to_int(bits[28:32])
        hum_units = bits_to_int(bits[32:36])
        humidity = hum_tens * 10 + hum_units
        if not 0 <= humidity <= 100:
            return None

        # Zero validation: byte4-lower through byte5 (bits 36-47)
        if bits_to_int(bits[36:48]) != 0:
            return None

        # Startup: lower nibble of byte6 (bits 52-55)
        startup = int(bits_to_int(bits[52:56]) != 0)

        # ID confirmation: byte7 (bits 56-63)
        if bits_to_int(bits[56:64]) != device_id:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id,
            "channel": channel,
            "battery_ok": int(battery_ok),
            "temperature_C": round(temp_c, 1),
            "humidity": humidity,
            "startup": startup,
        })


__all__ = ["BaldrTherm"]
