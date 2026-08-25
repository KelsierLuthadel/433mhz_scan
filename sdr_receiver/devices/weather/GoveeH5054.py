"""Govee Water Leak Detector H5054 (original) / Door Contact Sensor B5023."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


class GoveeH5054(OOKPWMDecoder):
    """Govee Water Leak Detector H5054 (original) / Door Contact Sensor B5023."""
    name     = "Govee-Water"
    short_us = 440.0
    long_us  = 940.0
    reset_us = 9_000.0
    n_bits   = 48

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Govee transmits with inverted polarity; invert before parsing.
        b = bytes(bits_to_int(bits[i:i + 8]) ^ 0xFF for i in range(0, 48, 8))

        device_id = (b[0] << 8) | b[1]
        if device_id == 0xFFFF or b[5] == 0:
            return None

        # Check full (pre-mask) event word for all-ones garbage
        raw_event = (b[2] << 8) | b[3]
        if raw_event == 0xFFFF:
            return None

        event_type = b[2] & 0x0F
        event      = raw_event & 0x0FFF  # strip upper nibble of b[2]

        # Parity field: byte 5 is laid out as  101PPPP1 → extract PPPP
        parity  = (b[5] >> 1) & 0x0F
        xor_val = b[0] ^ b[1] ^ b[2] ^ b[3] ^ b[4]
        chk     = ((xor_val >> 4) ^ (xor_val & 0x0F)) & 0x0F
        if chk != parity:
            return None

        # Battery is reported only in event_type 0xC
        battery    = b[3] if event_type == 0xC else 0
        battery_ok = round(battery * 0.01, 2)
        battery_mv = 1800 + 12 * battery

        wet   = None
        model = self.name

        if event == 0xAFA:
            event_str = "Button Press"
            wet = 0
        elif event == 0xBFB:
            event_str = "Water Leak"
            wet = 1
        elif event_type == 0xC:
            event_str = "Battery Report"
        elif event == 0xDFD:
            event_str = "Heartbeat"
        elif event == 0xE7F:
            model     = "Govee-Contact"
            event_str = "Open"
        else:
            event_str = "Unknown"

        fields: dict = {"id": device_id, "event": event_str}
        if battery:
            fields["battery_ok"] = battery_ok
            fields["battery_mV"] = battery_mv
        if wet is not None:
            fields["detect_wet"] = wet
        return DecodedPacket.from_fields(model, freq_hz, fields)


__all__ = ["GoveeH5054"]
