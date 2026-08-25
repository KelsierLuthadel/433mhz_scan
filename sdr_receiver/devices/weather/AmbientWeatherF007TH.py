"""Ambient Weather F007TH/F012TH, TFA 30.3208.02, SwitchDocLabs F016TH."""
from __future__ import annotations
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ._helpers import _lfsr_digest8
from ...packet import DecodedPacket


_PREAMBLE_NORM = [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0]   # 0x014 (12 bits of 0x0145)
_PREAMBLE_INV  = [1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0]   # 0xFD4 (12 bits of 0xFD45)


class AmbientWeatherF007TH(ManchesterDecoder):
    """Ambient Weather F007TH/F012TH, TFA 30.3208.02, SwitchDocLabs F016TH."""
    name     = "Ambientweather-F007TH"
    chip_us  = 500.0
    reset_us = 2_400.0
    n_bits   = 96   # generous to cover preamble + 3 repeats worth

    def _try_payload(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        """Attempt to decode a 48-bit payload starting at bit 0 of `bits`."""
        if len(bits) < 48:
            return None
        b = bytes(bits_to_int(bits[i:i + 8]) for i in range(0, 48, 8))
        expected   = b[5]
        calculated = _lfsr_digest8(b[:5], gen=0x98, key=0x3E) ^ 0x64
        if expected != calculated:
            return None

        device_id   = b[1]
        battery_low = bool(b[2] & 0x80)
        channel     = ((b[2] & 0x70) >> 4) + 1
        temp_raw    = ((b[2] & 0x0F) << 8) | b[3]
        temp_f      = (temp_raw - 400) * 0.1
        temp_c      = (temp_f - 32.0) * 5.0 / 9.0
        humidity    = b[4]

        if humidity > 100:
            return None
        if temp_f < -40.0 or temp_f >= 344.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Search for either preamble variant; data begins 8 bits after the
        # 12-bit pattern (i.e., the last 4 bits of the 12-bit preamble word
        # plus the following 44 bits form the 48-bit payload).
        for preamble in (_PREAMBLE_NORM, _PREAMBLE_INV):
            pos = 0
            while pos + 12 + 48 <= len(bits):
                if bits[pos:pos + 12] == preamble:
                    result = self._try_payload(bits[pos + 8:], freq_hz)
                    if result is not None:
                        return result
                    pos += 16
                else:
                    pos += 1
        # Fallback: try raw bits in case base class already stripped preamble
        return self._try_payload(bits, freq_hz)


__all__ = ["AmbientWeatherF007TH"]
