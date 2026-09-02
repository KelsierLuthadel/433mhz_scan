"""Roboguard / IQ-Blue PIR sensor decoder.

433.84 MHz OOK-PWM (inverted), short=1200 us, long=2400 us, reset=29700 us.
216 bits (27 bytes): 3-byte preamble + 8 x 3-byte payload repetitions.

The signal is inverted OOK: short pulse = logic 1, long pulse = logic 0.

Frame layout (after inversion):
  bytes[0:3]    Preamble  0x00 0x00 0x00
  bytes[3:6]   x8 reps   3-byte payload (majority-vote validated)

Payload (3 bytes):
  bits[7:4]   Signal type  0x2=heartbeat  0x4=tamper  0x5=remote  0xC=alert
  bits[3:0] + bytes[4:6]   Device ID (20-bit)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse

_SIGNAL_TYPES = {
    0x2: "heartbeat",
    0x4: "tamper",
    0x5: "remote",
    0xC: "alert",
}


class RoboguardIQBlue(OOKPWMDecoder):
    """Roboguard / IQ-Blue PIR security sensor."""
    name     = "Roboguard-IQBlue"
    short_us = 1200.0
    long_us  = 2400.0
    reset_us = 29700.0
    n_bits   = 216

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 216:
            return None

        # Inverted OOK: flip all bits
        bits = [1 - b for b in bits]

        # Preamble: first 24 bits must be 0x00 0x00 0x00
        if any(bits[i] != 0 for i in range(24)):
            return None

        # Extract 8 x 3-byte payload segments starting at byte 3
        segments: list[tuple[int, int, int]] = []
        for seg in range(8):
            off = (3 + seg * 3) * 8
            segments.append((
                bits_to_int(bits[off:off + 8]),
                bits_to_int(bits[off + 8:off + 16]),
                bits_to_int(bits[off + 16:off + 24]),
            ))

        # Majority vote: use first segment as reference, allow up to 3 mismatches
        ref = segments[0]
        mismatches = sum(1 for s in segments[1:] if s != ref)
        if mismatches > 3:
            return None

        signal_nibble = (ref[0] >> 4) & 0xF
        device_id = ((ref[0] & 0xF) << 16) | (ref[1] << 8) | ref[2]
        event = _SIGNAL_TYPES.get(signal_nibble, f"unknown_0x{signal_nibble:X}")

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":    f"{device_id:05X}",
            "event": event,
        })


__all__ = ["RoboguardIQBlue"]
