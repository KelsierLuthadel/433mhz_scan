"""LaCrosse TX141B / TX141-Bv2 / TX141TH-Bv2 / TX141TH-Bv3 (OOK PWM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ._helpers import _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseTX141x(OOKPWMDecoder):
    """LaCrosse TX141B / TX141-Bv2 / TX141TH-Bv2 / TX141TH-Bv3 (OOK PWM).

    Supports 32, 37, 40, and 41-bit variants detected by payload length.
    TX141TH variants include humidity + CRC-8 (poly 0x31, init 0xf4).
    """
    name     = "LaCrosse-TX141x"
    short_us = 208.0
    long_us  = 417.0
    reset_us = 1_700.0
    n_bits   = 32  # minimum; decode() tries all lengths

    def decode(self, pulses: list["Pulse"], freq_hz: float) -> DecodedPacket | None:
        from ...dsp import pulses_to_bits_pwm
        # Exclude sync pulses (~833 µs)  they sit between short and long thresholds
        data = [p for p in pulses
                if 50 < p.pulse_us < self.reset_us
                and not 620 < p.pulse_us < 1_100]
        for n_bits in (41, 40, 37, 32):
            if len(data) < n_bits:
                continue
            for off in range(min(5, len(data) - n_bits + 1)):
                bits = pulses_to_bits_pwm(
                    data[off : off + n_bits], self.short_us, self.long_us, 0.45
                )
                if bits is None:
                    continue
                result = self._parse_variant(bits, freq_hz, n_bits)
                if result is not None:
                    return result
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._parse_variant(bits, freq_hz, len(bits))

    def _parse_variant(self, bits: list[int], freq_hz: float,
                       n_bits: int) -> DecodedPacket | None:
        if n_bits < 32:
            return None

        sensor_id  = bits_to_int(bits[0:8])
        battery_ok = not bool(bits[8])
        channel    = bits_to_int(bits[10:12]) + 1
        temp_raw   = (bits_to_int(bits[12:16]) << 8) | bits_to_int(bits[16:24])
        temp_c     = (temp_raw - 500) / 10.0

        if not -40.0 <= temp_c <= 60.0:
            return None

        fields: dict = {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
        }

        if n_bits >= 40:
            # TX141TH-Bv2 / TX141TH-Bv3: byte 3 = humidity, byte 4 = CRC
            humidity = bits_to_int(bits[24:32])
            crc_recv = bits_to_int(bits[32:40])
            raw      = _extract_bytes(bits, 0, 4)
            if crc8(raw, poly=0x31, init=0xf4) != crc_recv:
                return None
            if 0 <= humidity <= 100:
                fields["humidity"] = humidity
            model = ("LaCrosse-TX141TH-Bv3" if n_bits == 41
                     else "LaCrosse-TX141TH-Bv2")
        elif n_bits == 37:
            model = "LaCrosse-TX141-Bv2"
        else:
            model = "LaCrosse-TX141B"

        return DecodedPacket.from_fields(model, freq_hz, fields)


__all__ = ["LaCrosseTX141x"]
