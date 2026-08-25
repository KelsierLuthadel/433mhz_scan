"""TFA-Twin-Plus-30.3049, Conrad KW9010, Ea2 BL999."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _reverse8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFATwinPlus303049(OOKPPMDecoder):
    """TFA-Twin-Plus-30.3049, Conrad KW9010, Ea2 BL999.

    OOK_PPM, short=2000 us, long=4000 us, gap=6000 us, reset=10000 us.
    36 bits: each byte is bit-reversed before interpretation.
    Layout after reversal: ID(6) | channel(2) | battery(1) | cfg(3)
                           | temp(9) | sign(3) | humidity(7) | checksum(4).
    Checksum: lower nibble of sum of all 8 nibbles in reversed bytes 0–3.
    Temperature: negative when original b[2] & 7 != 0; value = -(512-temp)*0.1.
    Humidity: (rb[3] & 0x7F) - 28.
    """
    name      = "TFA-TwinPlus"
    short_us  = 2000.0
    long_us   = 4000.0
    reset_us  = 10000.0
    n_bits    = 36
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None

        # 4 full bytes + last nibble stored in upper half of a 5th byte
        b = [bits_to_int(bits[i * 8:(i + 1) * 8]) for i in range(4)]
        b.append(bits_to_int(bits[32:36]) << 4)

        if not any(b):
            return None

        rb = [_reverse8(x) for x in b]

        sum_nibbles = sum((rb[i] >> 4) + (rb[i] & 0x0F) for i in range(4))
        checksum    = rb[4] & 0x0F
        if (sum_nibbles & 0x0F) != checksum:
            return None

        # negative_sign uses the original (non-reversed) byte 2, bits 2-0
        negative_sign = b[2] & 7
        temp      = ((rb[2] & 0x1F) << 4) | (rb[1] >> 4)
        humidity  = (rb[3] & 0x7F) - 28
        sensor_id = (rb[0] & 0x0F) | ((rb[0] & 0xC0) >> 2)
        battery_low = (b[1] >> 7) & 1   # original byte 1 MSB
        channel     = (b[0] >> 2) & 3   # original byte 0, bits 3-2

        temp_c = (-(512 - temp) if negative_sign else temp) * 0.1

        if not -40.0 <= temp_c <= 60.0:
            return None
        if not 0 <= humidity <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    int(not battery_low),
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["TFATwinPlus303049"]
