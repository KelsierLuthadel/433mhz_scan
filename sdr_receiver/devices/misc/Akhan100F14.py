"""Akhan 100F14 Car Remote (OOK_PULSE_PWM, 25 bits)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Akhan100F14(OOKPWMDecoder):
    """Akhan 100F14 Remote Keyless Entry (HS1527 OTP encoder)."""
    name     = "Akhan-100F14"
    short_us = 316.0
    long_us  = 1020.0
    reset_us = 1800.0
    n_bits   = 25

    _COMMANDS = {0x1: "Lock", 0x2: "Unlock", 0x4: "Mute", 0x8: "Alarm"}

    def _parse(self, bits, freq_hz):
        if len(bits) < 25:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, 24, 8)]
        b = [v ^ 0xFF for v in b]                      # invert all bits
        device_id = (b[0] << 12) | (b[1] << 4) | (b[2] >> 4)
        cmd = b[2] & 0x0F
        if cmd not in self._COMMANDS:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz,
            {"id": device_id, "cmd": self._COMMANDS[cmd]})


__all__ = ["Akhan100F14"]
