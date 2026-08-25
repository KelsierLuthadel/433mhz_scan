"""LaCrosse/ELV/Conrad WS7000 / WS2500 weather sensors (OOK PWM, nibble-based)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseWS7000(OOKPWMDecoder):
    """LaCrosse/ELV/Conrad WS7000 / WS2500 weather sensors (OOK PWM, nibble-based).

    Preamble: 10× '0' bits followed by a '1' start bit.
    Format:   TYPE(1 nib) ADDR(1 nib) DATA(3-6 nibs) XOR(1 nib) ADD(1 nib)
    Sensor types: 0=temp, 1=temp+hum, 2=rain, 3=wind, 4=temp+hum+pressure, 5=lux.
    Integrity: XOR nibble + additive nibble ((sum+5) & 0xF).
    """
    name     = "LaCrosse-WS7000"
    short_us = 400.0
    long_us  = 800.0
    reset_us = 1_100.0
    n_bits   = 8  # placeholder  decode() handles variable length

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        from ...dsp import pulses_to_bits_pwm
        data = [p for p in pulses if 50 < p.pulse_us < self.reset_us]
        if len(data) < 16:
            return None
        bits = pulses_to_bits_pwm(data, self.short_us, self.long_us, 0.45)
        if bits is None or len(bits) < 16:
            return None
        return self._parse(bits, freq_hz)

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Find start bit (first '1' after a run of '0' preamble bits)
        start = -1
        for i in range(len(bits) - 1):
            if bits[i] == 1 and i >= 3 and all(b == 0 for b in bits[max(0, i - 10) : i]):
                start = i + 1
                break
        if start < 0:
            return None

        nibbles = [bits_to_int(bits[start + i : start + i + 4])
                   for i in range(0, len(bits) - start - 3, 4)]
        if len(nibbles) < 4:
            return None

        sensor_type = nibbles[0]
        addr_nib    = nibbles[1]
        address     = addr_nib & 0x7
        neg_temp    = bool(addr_nib & 0x8)

        data_len = {0: 3, 1: 5, 2: 3, 3: 5, 4: 6, 5: 6}.get(sensor_type)
        if data_len is None:
            return None
        if len(nibbles) < 2 + data_len + 2:
            return None

        data_nibs = nibbles[2 : 2 + data_len]
        xor_nib   = nibbles[2 + data_len]
        add_nib   = nibbles[2 + data_len + 1]

        # XOR checksum
        xor_val = sensor_type ^ addr_nib
        for n in data_nibs:
            xor_val ^= n
        if xor_val != xor_nib:
            return None

        # Additive checksum: (all nibbles so far + 5) & 0xF
        total = (sensor_type + addr_nib + sum(data_nibs) + xor_nib + 5) & 0xF
        if total != add_nib:
            return None

        channel = address + 1
        fields: dict = {"channel": channel}

        if sensor_type in (0, 1):
            temp_raw = data_nibs[0] * 100 + data_nibs[1] * 10 + data_nibs[2]
            temp_c   = temp_raw / 10.0 * (-1 if neg_temp else 1)
            if not -40.0 <= temp_c <= 80.0:
                return None
            fields["temperature_C"] = round(temp_c, 1)
            if sensor_type == 1:
                hum = data_nibs[3] * 10 + data_nibs[4]
                if 0 <= hum <= 100:
                    fields["humidity"] = hum
            model = "LaCrosse-WS7000-20" if sensor_type == 1 else "LaCrosse-WS7000-15"

        elif sensor_type == 2:
            rain_raw = data_nibs[0] * 100 + data_nibs[1] * 10 + data_nibs[2]
            fields["rain_mm"] = round(rain_raw * 0.5, 1)
            model = "LaCrosse-WS7000-16"

        elif sensor_type == 3:
            wind_spd = (data_nibs[0] * 100 + data_nibs[1] * 10 + data_nibs[2]) / 10.0
            wind_dir = (data_nibs[3] * 10 + data_nibs[4]) * 22.5
            fields.update({"wind_avg_m_s": round(wind_spd, 1), "wind_dir_deg": wind_dir})
            model = "LaCrosse-WS7000-17"

        elif sensor_type == 4:
            temp_raw = data_nibs[0] * 100 + data_nibs[1] * 10 + data_nibs[2]
            temp_c   = temp_raw / 10.0 * (-1 if neg_temp else 1)
            hum      = data_nibs[3] * 10 + data_nibs[4]
            # Pressure: simplified (actual encoding is more complex)
            pressure = data_nibs[5] * 10 + 200
            fields.update({"temperature_C": round(temp_c, 1),
                           "humidity": hum, "pressure_hPa": pressure})
            model = "LaCrosse-WS7000-27"

        elif sensor_type == 5:
            exp      = data_nibs[2]
            mantissa = data_nibs[0] * 10 + data_nibs[1]
            fields["lux"] = mantissa * (10 ** exp)
            model = "LaCrosse-WS7000-28"

        else:
            return None

        return DecodedPacket.from_fields(model, freq_hz, fields)


__all__ = ["LaCrosseWS7000"]
