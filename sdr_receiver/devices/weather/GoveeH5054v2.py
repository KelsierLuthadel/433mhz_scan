"""Govee Water Leak Detector H5054 (2021+ board revision, CRC-16)."""
from __future__ import annotations
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket


class GoveeH5054v2(OOKPWMDecoder):
    """Govee Water Leak Detector H5054 (2021+ board revision, CRC-16)."""
    name     = "Govee-Water"
    short_us = 440.0
    long_us  = 940.0
    reset_us = 9_000.0
    n_bits   = 48

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        b = bytes(bits_to_int(bits[i:i + 8]) ^ 0xFF for i in range(0, 48, 8))

        # CRC-16/AUG-CCITT residue check over all 6 bytes (non-reflected)
        if crc16(b, poly=0x1021, init=0x1D0F, ref_in=False, ref_out=False) != 0:
            return None

        device_id  = (b[0] << 8) | b[1]
        event      = b[2] & 0x0F
        event_data = b[3]

        wet      = None
        leak_num = None
        battery  = -1

        if event == 0x0:
            event_str = "Button Press"
            wet = 0
        elif event == 0x1:
            event_str = "Battery Report"
            battery   = event_data
        elif event == 0x2:
            event_str = "Water Leak"
            wet       = 1
            leak_num  = event_data
        else:
            event_str = "Unknown"

        fields: dict = {"id": device_id, "event": event_str}
        if battery >= 0:
            fields["battery_ok"] = round(battery * 0.01, 2)
            fields["battery_mV"] = 1800 + 12 * battery
        if wet is not None:
            fields["detect_wet"] = wet
        if leak_num is not None:
            fields["leak_num"] = leak_num
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["GoveeH5054v2"]
