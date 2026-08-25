"""WEC-2103 wireless temperature/humidity sensor."""
from __future__ import annotations
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


class WEC2103(OOKPPMDecoder):
    """WEC-2103 wireless temperature/humidity sensor.

    Modulation: OOK_PULSE_PPM
    short_us=1900 (gap=0), long_us=3800 (gap=1), reset_us=9400, n_bits=40
    The rtl_433 decoder finds the data row (row 3 of 6) with 40 bits.

    Bit layout (40 bits):
      byte 0       : device ID
      byte 1 hi    : 4-bit checksum nibble
      byte 1 lo    : 4-bit flags (bit2=battery_low, bit3=button)
      byte 2       : temperature high 8 bits
      byte 3 hi    : temperature low 4 bits
      byte 3 lo    : humidity high nibble
      byte 4 hi    : humidity low nibble
      byte 4 lo    : channel nibble

    Temperature (°F): ((temp_raw - 900) * 0.1), temp_raw = (byte2 << 4) | byte3_hi
    Humidity (%): hum_lo * 10 + hum_hi  (note: reversed digit order in BCD)
    Checksum: nibble XOR across all nibbles should equal 0 (approximation of CRC-4 poly=3, init=0).
    """

    name = "WEC-2103"
    short_us = 1900.0
    long_us = 3800.0
    reset_us = 9400.0
    n_bits = 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        device_id = bits_to_int(bits[0:8])
        chk_nibble = bits_to_int(bits[8:12])
        flags = bits_to_int(bits[12:16])
        temp_high = bits_to_int(bits[16:24])
        temp_lo_nib = bits_to_int(bits[24:28])
        hum_hi_nib = bits_to_int(bits[28:32])
        hum_lo_nib = bits_to_int(bits[32:36])
        channel = bits_to_int(bits[36:40])

        # Nibble XOR validation: XOR all 10 nibbles (including checksum nibble) → 0
        nibbles = [bits_to_int(bits[i:i + 4]) for i in range(0, 40, 4)]
        xor_all = 0
        for n in nibbles:
            xor_all ^= n
        if xor_all != 0:
            return None

        # Temperature in Fahrenheit
        temp_raw = (temp_high << 4) | temp_lo_nib
        temp_f = (temp_raw - 900) * 0.1
        if not -40.0 <= temp_f <= 160.0:
            return None

        # Humidity: low digit * 10 + high digit (inverted BCD)
        humidity = hum_lo_nib * 10 + hum_hi_nib
        if not 0 <= humidity <= 100:
            return None

        battery_ok = not bool((flags >> 2) & 1)
        button = bool((flags >> 3) & 1)

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device_id,
            "channel": channel,
            "battery_ok": int(battery_ok),
            "button": int(button),
            "temperature_F": round(temp_f, 1),
            "humidity": humidity,
            "flags": flags,
        })


__all__ = ["WEC2103"]
