"""TFA pool temperature sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TFAPoolThermometer(OOKPPMDecoder):
    """TFA pool temperature sensor.

    OOK_PPM, short=2000 us, long=4600 us, gap=7800 us, reset=10000 us.
    28 bits: checksum(4) | ID(8) | temp(12) | channel(2) | battery(1) | x(1).
    Checksum: (sum of nibbles 1–6) - 1, lower nibble == nibble 0.
    Temperature: raw > 2048 → raw - 4096; result * 0.1 °C.
    """
    name      = "TFA-Pool"
    short_us  = 2000.0
    long_us   = 4600.0
    reset_us  = 10000.0
    n_bits    = 28
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 28:
            return None

        # Seven nibbles (0–6)
        nib = [bits_to_int(bits[i * 4:(i + 1) * 4]) for i in range(7)]

        checksum_rx = nib[0]
        checksum    = (sum(nib[1:7]) - 1) & 0x0F
        if checksum_rx != checksum:
            return None

        device   = (nib[1] << 4) | nib[2]
        temp_raw = (nib[3] << 8) | (nib[4] << 4) | nib[5]
        temp_c   = (temp_raw - 4096 if temp_raw > 2048 else temp_raw) * 0.1

        # nib[6] = bits[24:28] msb-first: bit7→bit6 = channel, bit5 = battery
        channel = (nib[6] >> 2) & 3
        battery = (nib[6] >> 1) & 1

        if not -40.0 <= temp_c <= 60.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device,
            "channel":       channel,
            "battery_ok":    battery,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["TFAPoolThermometer"]
