"""NewKAKU / KAKU self-learning mains socket remote (ARC protocol) decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class NewKAKU(RawDecoder):
    """NewKAKU / KAKU self-learning mains socket remote (ARC protocol).

    OOK_PULSE_PPM, short=300 µs, long=1400 µs, sync=2650 µs, reset=3200 µs.
    PPM symbols decoded as Manchester pairs: 01→0, 10→1, 11→1 (DIM).
    36 decoded bits: id[26] | group[1] | state[1] | unit[4] | dim[4 optional].
    No checksum.
    """
    name     = "NewKAKU"
    _SHORT   = 300.0
    _LONG    = 1400.0
    _SYNC    = 2650.0
    _TOL     = 0.40

    def _near(self, val: float, ref: float) -> bool:
        return abs(val - ref) / (ref + 1.0) < self._TOL

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        if len(pulses) < 75:
            return None
        # find sync gap
        start = -1
        for i, p in enumerate(pulses):
            if self._near(p.gap_us, self._SYNC):
                start = i + 1
                break
        if start < 0:
            return None
        # collect PPM symbols from gaps
        raw: list[int] = []
        for p in pulses[start:]:
            if self._near(p.gap_us, self._SHORT):
                raw.append(0)
            elif self._near(p.gap_us, self._LONG):
                raw.append(1)
            else:
                break
        if len(raw) < 64:
            return None
        # Manchester decode: (0,1)→0, (1,0)→1, (1,1)→DIM=1
        decoded: list[int] = []
        dim = False
        j = 0
        while j + 1 < len(raw):
            a, bb = raw[j], raw[j + 1]
            if a == 0 and bb == 1:
                decoded.append(0)
            elif a == 1 and bb == 0:
                decoded.append(1)
            elif a == 1 and bb == 1:
                decoded.append(1)
                dim = True
            else:
                return None
            j += 2
        if len(decoded) < 32:
            return None
        device_id = bits_to_int(decoded[0:26])
        group     = decoded[26]
        state     = decoded[27]
        unit      = bits_to_int(decoded[28:32])
        fields: dict = {
            "id":    device_id,
            "group": group,
            "state": "on" if state else "off",
            "unit":  unit + 1,
        }
        if dim and len(decoded) >= 36:
            fields["dim_level"] = bits_to_int(decoded[32:36])
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["NewKAKU"]
