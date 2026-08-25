"""Bresser Lightning Distance Sensor (FSK PCM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ._helpers import _lfsr_digest16, _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


_LIGHTNING_SENSOR_TYPE = 9   # SENSOR_TYPE_LIGHTNING in rtl_433 source


class BresserLightning(FSKPCMDecoder):
    """Bresser Lightning Distance Sensor (FSK PCM).

    Preamble: AA AA 2D D4  (4 bytes)
    Payload:  10 bytes, XOR-whitened with 0xAA.
    Integrity: LFSR-16 keyed digest with key 0xABF9, XOR'd against 0x899E.
    """
    name     = "Bresser-Lightning"
    bit_rate = 1_000_000.0 / 124.0
    n_bits   = 440

    _PREAMBLE = bytes([0xAA, 0xAA, 0x2D, 0xD4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        start = _find_preamble(bits, self._PREAMBLE)
        if start < 0:
            return None

        raw = _extract_bytes(bits, start, 10)
        if raw is None:
            return None

        # Remove XOR whitening
        msg = bytes(b ^ 0xAA for b in raw)

        # LFSR-16 integrity check: (chk ^ digest) must equal 0x899E
        chk    = (msg[0] << 8) | msg[1]
        digest = _lfsr_digest16(msg[2:10], 0x8810, 0xABF9)
        if (chk ^ digest) != 0x899E:
            return None

        sensor_id   = (msg[2] << 8) | msg[3]
        # Strike count: 3 BCD digits spanning the upper nibbles of bytes 4 and 5
        count       = (msg[4] >> 4) * 100 + (msg[4] & 0x0F) * 10 + (msg[5] >> 4)
        battery_ok  = not bool((msg[5] & 0x08) >> 3)
        nstartup    = bool((msg[6] & 0x08) >> 3)
        s_type      = msg[6] >> 4
        chan        = msg[6] & 0x07
        distance_km = msg[7]

        if s_type != _LIGHTNING_SENSOR_TYPE or chan != 0:
            return None

        fields: dict = {
            "id":           sensor_id,
            "battery_ok":   battery_ok,
            "strike_count": count,
            "distance_km":  distance_km,
        }
        if nstartup:
            fields["startup"] = 1

        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["BresserLightning"]
