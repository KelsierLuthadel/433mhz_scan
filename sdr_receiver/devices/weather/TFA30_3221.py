"""TFA Dostmann 30.3221.02 T/H Outdoor Sensor (also 30.3249.02)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ._helpers import _reverse8, _lfsr_digest8_reflect
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFA30_3221(OOKPWMDecoder):
    """TFA Dostmann 30.3221.02 T/H Outdoor Sensor (also 30.3249.02).

    OOK_PWM, short=235 us, long=480 us, reset=850 us, sync=836 us.
    40 bits: ID(8) | cfg(8) | temp(12) | humidity(8) | checksum(8).
    Checksum: lfsr_digest8_reflect(bytes[0:4], gen=0x31, key=0xf4).
    Signal is transmitted inverted relative to PWM convention.
    """
    name      = "TFA-303221"
    short_us  = 235.0
    long_us   = 480.0
    reset_us  = 850.0
    n_bits    = 40
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # rtl_433 calls bitbuffer_invert() before reading  flip bits here.
        bits = [1 - v for v in bits]

        b = bytearray(bits_to_int(bits[i * 8:(i + 1) * 8]) for i in range(5))

        device = b[0]
        if device == 0:
            return None

        if _lfsr_digest8_reflect(b, 4, 0x31, 0xF4) != b[4]:
            return None

        temp_raw    = ((b[1] & 0x0F) << 8) | b[2]
        temp_c      = (temp_raw - 500) * 0.1
        humidity    = b[3]
        battery_low = (b[1] >> 7) & 1
        channel     = ((b[1] >> 4) & 3) + 1
        sendmode    = (b[1] >> 6) & 1

        if not -50.0 <= temp_c <= 70.0:
            return None
        if not 0 <= humidity <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
            "sendmode":      sendmode,
        })


__all__ = ["TFA30_3221"]
