"""Elster / Honeywell AMR power meter  ported from rtl_433 C source.

Note: elster.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ElsterPowerMeter(RawDecoder):
    """Elster / Honeywell AMR power meter (FSK_PULSE_MANCHESTER_ZEROBIT, ~35 kbps).

    Type-1 frame: whitening XOR 0x55, CRC-16/X-25 (poly 0x8408, init 0xFFFF).
        LEN(8) FLAG(8) SRC(32) DST(32) ... DATA CRC(16)
        Fields: id, dst, frame_type, ctr, cur_hour_kWh, reading_kWh.
    Type-2 frame (4× faster variant): whitening XOR 0xAA.
        LEN(16) ... SRC(32) DST(32) ... DATA CRC(16)
        Fields: id, dst, mesh_id, msg_type, data_raw.
    """
    name = "Elster-PowerMeter"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None  # FSK Manchester path only


__all__ = ["ElsterPowerMeter"]
