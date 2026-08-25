"""TFA Drop Rain Gauge 30.3233.01."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ._helpers import _reverse8, _lfsr_digest8_reflect
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFADrop303233(OOKPWMDecoder):
    """TFA Drop Rain Gauge 30.3233.01.

    OOK_PWM, short=255 us, long=510 us, sync=750 us, reset=2500 us.
    66 bits (inverted): prefix(4)=0x3 | ID(20) | flags(8) | rain_lo(8)
                        | const_AA(8) | rain_hi(8) | checksum(8) | unused(2).
    Checksum: lfsr_digest8_reflect(bytes[0:7], gen=0x31, key=0xf4).
    Rain (mm) = (rain_hi<<8 | rain_lo + 10) * 0.254.
    """
    name      = "TFA-Drop"
    short_us  = 255.0
    long_us   = 510.0
    reset_us  = 2500.0
    n_bits    = 66
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # rtl_433 calls bitbuffer_invert() before reading  flip bits here.
        bits = [1 - v for v in bits]

        if len(bits) < 66:
            return None

        # 8 full bytes carry all validated fields; trailing 2 bits are ignored.
        b = bytearray(bits_to_int(bits[i * 8:(i + 1) * 8]) for i in range(8))

        # Upper nibble of byte 0 must be 0x3 (start marker).
        if (b[0] & 0xF0) != 0x30:
            return None

        if _lfsr_digest8_reflect(b, 7, 0x31, 0xF4) != b[7]:
            return None

        sensor_id   = ((b[0] & 0x0F) << 16) | (b[1] << 8) | b[2]
        battery_low = (b[3] & 0x80) >> 7
        # Rain counter: little-endian (low byte at index 4, high byte at index 6).
        rain_counter = (b[6] << 8) | b[4]
        rain_counter += 10          # hardware offset per rtl_433 source
        rain_mm = rain_counter * 0.254

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":         sensor_id,
            "battery_ok": int(not battery_low),
            "rain_mm":    round(rain_mm, 1),
        })


__all__ = ["TFADrop303233"]
