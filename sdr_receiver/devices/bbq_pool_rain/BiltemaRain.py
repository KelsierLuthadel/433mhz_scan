"""Biltema Rain Gauge (bt_rain)  ported from rtl_433 C source.

Note: biltema_rain.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from .._helpers import _bits_to_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BiltemaRain(OOKPPMDecoder):
    """Biltema Rain Gauge (bt_rain).

    OOK_PULSE_PPM, 36 bits.
    Layout: ID(8) BAT(1) CH(2) BTN(1) TEMP(11) RAIN/TEMP_SHARED RAIN(8)
    No checksum  disabled by default in rtl_433 due to uncertain layout.
    """

    name     = "Biltema-Rain"
    short_us = 1940.0
    long_us  = 3900.0
    reset_us = 8800.0
    n_bits   = 36

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 36:
            return None
        b = _bits_to_bytes(bits[:36])
        if len(b) < 4:
            return None
        if b[0] == 0xFF and b[1] == 0xFF and b[2] == 0xFF and b[3] == 0xFF:
            return None
        id_      = b[0]
        battery  = b[1] >> 7
        channel  = ((b[1] & 0x30) >> 4) + 1
        button   = (b[1] & 0x08) >> 3
        # 11-bit signed temperature from bits[13:24]
        t_raw = ((b[1] & 0x07) << 8) | b[2]
        if t_raw >= 1024:
            t_raw -= 2048
        temp_c   = round(t_raw * 0.1, 1)
        # Rain rate  uncertain layout per C source comment
        rain     = ((b[1] & 0x07) << 4) | b[3]
        rest     = rain % 25
        if rest % 2:
            rain += (rest // 2) * 2048
        else:
            rain += ((rest + 1) // 2) * 2048 + 12 * 2048
        rain_mm_h = round(rain * 0.052, 2)
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           id_,
            "channel":      channel,
            "battery_ok":   int(not battery),
            "button":       button,
            "temperature_C": temp_c,
            "rain_rate_mm_h": rain_mm_h,
        })


__all__ = ["BiltemaRain"]
