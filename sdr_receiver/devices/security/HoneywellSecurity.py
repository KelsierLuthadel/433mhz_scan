"""Honeywell 5800 / 2Gig DW10/DW11 / RE208 security sensor decoder."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HoneywellSecurity(ManchesterDecoder):
    """Honeywell 5800 / 2Gig DW10/DW11 / RE208 (OOK_PULSE_PCM Manchester, 136 µs chip).

    Preamble 0xFFFE (Manchester), then 64-bit payload with CRC-16.
    """

    name      = "Honeywell-Security"
    chip_us   = 136.0
    reset_us  = 408.0
    n_bits    = 80   # 16 preamble + 64 payload
    tolerance = 0.45

    _PREAMBLE = [1] * 15 + [0]  # 0xFFFE

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        found = -1
        for s in range(min(32, len(bits) - 64)):
            if bits[s : s + 16] == self._PREAMBLE:
                found = s + 16
                break
        if found < 0 or found + 64 > len(bits):
            return None
        p = bits[found : found + 64]
        channel    = bits_to_int(p[0:4])
        device_id  = bits_to_int(p[4:24])
        event_byte = bits_to_int(p[24:32])
        crc_recv   = bits_to_int(p[32:48])
        raw4 = bytes([
            (channel << 4) | ((device_id >> 16) & 0xF),
            (device_id >> 8) & 0xFF,
            device_id & 0xFF,
            event_byte,
        ])
        poly = 0x8050 if channel in (0x2, 0x4, 0x9, 0xA, 0xC) else 0x8005
        crc_ok = any(
            crc16(raw4, poly=poly, init=0, ref_in=r, ref_out=r) == crc_recv
            for r in (False, True)
        )
        if not crc_ok:
            return None
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           f"{device_id:05X}",
            "channel":      channel,
            "contact_open": int(bool(event_byte & 0x80)),
            "tamper":       int(bool(event_byte & 0x04)),
            "alarm":        int(bool(event_byte & 0x01)),
            "battery_ok":   int(not bool(event_byte & 0x08)),
            "heartbeat":    int(bool(event_byte & 0x40)),
            "event":        event_byte,
            "mic":          "CRC",
        })


__all__ = ["HoneywellSecurity"]
