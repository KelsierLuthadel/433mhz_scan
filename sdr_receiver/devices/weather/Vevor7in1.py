"""Vevor Wireless Weather Station 7-in-1."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class Vevor7in1(RawDecoder):
    """Vevor Wireless Weather Station 7-in-1.

    Modulation: FSK_PULSE_PCM, chip_us=87, reset_us=9000
    33-byte packet; preamble AA AA CA CA 54; checksum = sum(bytes[0..18]) mod 256 == bytes[19].

    Fields: channel, ID, battery_low, temperature_C, humidity, wind_avg_km_h,
            wind_gust_km_h, wind_dir_deg, rain_mm, uv_index, illuminance_lux.
    FSK modulation is not supported by OOK base classes; stub returns None.
    """

    name = "Vevor-7in1"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:  # type: ignore[override]
        return None


__all__ = ["Vevor7in1"]
