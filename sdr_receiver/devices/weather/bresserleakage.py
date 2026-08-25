"""Bresser Water Leakage Sensor (FSK PCM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc16
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


_LEAKAGE_SENSOR_TYPE = 9   # SENSOR_TYPE_LEAKAGE in rtl_433 source


class BresserLeakage(FSKPCMDecoder):
    """Bresser Water Leakage Sensor (FSK PCM).

    Preamble: AA AA 2D D4  (4 bytes)
    Payload:  18 bytes.
    CRC-16/XMODEM: poly 0x1021, init 0x0000, non-reflected,
                   over bytes 2–6 (5 bytes); result compared to bytes 0–1.
    """
    name     = "Bresser-Leakage"
    bit_rate = 1_000_000.0 / 124.0
    n_bits   = 440

    _PREAMBLE = bytes([0xAA, 0xAA, 0x2D, 0xD4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        start = _find_preamble(bits, self._PREAMBLE)
        if start < 0:
            return None

        msg = _extract_bytes(bits, start, 18)
        if msg is None:
            return None

        # CRC-16/XMODEM over bytes 2–6
        crc_recv = (msg[0] << 8) | msg[1]
        if crc16(msg[2:7], poly=0x1021, init=0x0000, ref_in=False, ref_out=False) != crc_recv:
            return None

        sensor_id  = (msg[2] << 24) | (msg[3] << 16) | (msg[4] << 8) | msg[5]
        s_type     = msg[6] >> 4
        nstartup   = bool((msg[6] & 0x08) >> 3)
        chan       = msg[6] & 0x07
        battery_ok = (msg[7] & 0x30) != 0x00
        alarm      = bool((msg[7] & 0x80) >> 7)
        no_alarm   = bool((msg[7] & 0x40) >> 6)

        # Sanity: must be leakage sensor type, alarm and no_alarm cannot match,
        # and channel must be non-zero.
        if s_type != _LEAKAGE_SENSOR_TYPE or alarm == no_alarm or chan == 0:
            return None

        fields: dict = {
            "id":         f"{sensor_id:08x}",
            "channel":    chan,
            "battery_ok": battery_ok,
            "alarm":      alarm,
        }
        if nstartup:
            fields["startup"] = 1

        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["BresserLeakage"]
