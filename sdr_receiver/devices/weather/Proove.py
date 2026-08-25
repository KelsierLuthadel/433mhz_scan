"""Proove / Nexa / KlikAanKlikUit 64-bit wireless switch."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Proove(OOKPPMDecoder):
    """Proove / Nexa / KlikAanKlikUit 64-bit wireless switch."""
    name      = "Proove"
    short_us  = 270.0
    long_us   = 1300.0
    reset_us  = 2800.0
    tolerance = 0.45
    n_bits    = 64

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # The 64 PPM bits encode a Manchester stream → decode to 32 data bits
        data: list[int] = []
        for i in range(0, len(bits) - 1, 2):
            a, b = bits[i], bits[i + 1]
            if a == 0 and b == 1:
                data.append(0)
            elif a == 1 and b == 0:
                data.append(1)
            else:
                return None  # invalid Manchester symbol
        if len(data) < 32:
            return None
        house_id = bits_to_int(data[0:26])
        group    = bool(data[26])
        on_off   = bool(data[27])
        channel  = (~bits_to_int(data[28:30])) & 0x03
        unit     = (~bits_to_int(data[30:32])) & 0x03
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": house_id, "channel": channel + 1, "unit": unit + 1,
            "group": group, "state": on_off,
        })


__all__ = ["Proove"]
