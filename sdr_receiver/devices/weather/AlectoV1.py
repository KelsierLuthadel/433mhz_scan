"""AlectoV1 weather sensor  Alecto WS3500/WS4500/WS-1050, Ventus W155/W044."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ._helpers import _reverse8, _sign16_top12
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _alecto_checksum(b: list[int]) -> bool:
    """Alecto nibble-sum checksum over reversed bytes 0-3."""
    csum = 0
    for i in range(4):
        tmp = _reverse8(b[i])
        csum += (tmp & 0xF) + ((tmp >> 4) & 0xF)
    if (b[1] & 0x7F) == 0x6C:
        csum = (csum + 7) & 0xFF
    else:
        csum = (0xF - csum) & 0xFF
    csum = _reverse8((csum & 0xF) << 4)
    return csum == (b[4] >> 4)


class AlectoV1(OOKPPMDecoder):
    """AlectoV1 weather sensor  Alecto WS3500/WS4500/WS-1050, Ventus W155/W044."""
    name     = "AlectoV1"
    short_us = 2_000.0
    long_us  = 4_000.0
    reset_us = 10_000.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None

        # Low nibble of last byte must be zero
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 32, 8)] + \
            [bits_to_int(bits[32:36]) << 4]  # b[4] upper nibble only

        if (b[4] & 0x0F) != 0:
            return None

        if not _alecto_checksum(b):
            return None

        battery_ok = int(not ((b[1] & 0x80) >> 7))
        msg_type   = (b[1] & 0x60) >> 5
        channel    = (b[0] & 0x0C) >> 2
        sensor_id  = _reverse8(b[0])

        if msg_type != 3:
            # Temperature / humidity message
            r1 = _reverse8(b[1])
            r2 = _reverse8(b[2])
            r3 = _reverse8(b[3])

            t16    = (r1 & 0xF0) | (r2 << 8)
            temp_c = _sign16_top12(t16) * 0.1

            # BCD humidity
            humidity = ((r3 >> 4) & 0xF) * 10 + (r3 & 0xF)

            if not -50.0 <= temp_c <= 80.0:
                return None
            if not 0 <= humidity <= 100:
                return None

            return DecodedPacket.from_fields(self.name, freq_hz, {
                "id":            sensor_id,
                "channel":       channel,
                "battery_ok":    battery_ok,
                "temperature_C": round(temp_c, 1),
                "humidity":      humidity,
            })

        else:
            # Rain message: check for wind pattern vs rain by looking at data
            r2 = _reverse8(b[2])
            r3 = _reverse8(b[3])
            rain_mm = ((r3 << 8) | r2) * 0.25

            return DecodedPacket.from_fields(self.name + "-Rain", freq_hz, {
                "id":         sensor_id,
                "channel":    channel,
                "battery_ok": battery_ok,
                "rain_mm":    round(rain_mm, 2),
            })


__all__ = ["AlectoV1"]
