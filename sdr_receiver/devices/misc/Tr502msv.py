"""TR-502MSV Remote Controller (OOK_PULSE_PWM, 21 bits)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Tr502msv(OOKPWMDecoder):
    """TR-502MSV Remote Controller (mains socket remote)."""
    name     = "TR-502MSV"
    short_us = 740.0
    long_us  = 1400.0
    reset_us = 84000.0
    n_bits   = 21

    # socket_id raw → physical socket (0 = ALL)
    _SOCKET_MAP = {0: 1, 2: 2, 4: 3, 6: 4, 7: 0}

    def _parse(self, bits, freq_hz):
        if len(bits) < 21:
            return None
        if bits[0] != 1:                   # preamble bit
            return None
        device_id = bits_to_int(bits[1:13])
        socket_id = bits_to_int(bits[13:16])
        on_off    = bits[16]
        command   = bits[17]
        if bits[18] != 0:                  # reserved bit
            return None
        chk_recv = bits_to_int(bits[19:21])
        s0, s1, s2 = bits[15], bits[14], bits[13]
        u1 = command ^ s2 ^ s0
        u0 = on_off ^ s1
        if chk_recv != ((u1 << 1) | u0):
            return None
        if socket_id not in self._SOCKET_MAP:
            return None
        socket = self._SOCKET_MAP[socket_id]
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":     device_id,
            "socket": socket if socket else "ALL",
            "state":  "on" if on_off else "off",
            "mic":    "CHECKSUM",
        })


__all__ = ["Tr502msv"]
