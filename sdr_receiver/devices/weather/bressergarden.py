"""Bresser SmartHome Garden soil moisture / water timer valve (FSK PCM)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc16
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class BresserGarden(FSKPCMDecoder):
    """Bresser SmartHome Garden soil moisture / water timer valve (FSK PCM).

    Preamble: AA F3 E9 10 5E 51  (6 bytes)
    Payload:  33 bytes (includes 2-byte CRC-16 at the end).
    CRC-16/CCITT-FALSE: poly 0x1021, init 0xD636, non-reflected, over all 33 bytes.

    This is a complex multi-type protocol (20+ message types for valve control,
    soil readings, time programming, etc.).  This stub validates the CRC and
    returns the raw bytes together with the target/source IDs and message type
    for higher-level application processing.
    """
    name     = "Bresser-Garden"
    bit_rate = 1_000_000.0 / 50.0   # ~20 kbps
    n_bits   = 512

    _PREAMBLE = bytes([0xAA, 0xF3, 0xE9, 0x10, 0x5E, 0x51])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        start = _find_preamble(bits, self._PREAMBLE)
        if start < 0:
            return None

        msg = _extract_bytes(bits, start, 33)
        if msg is None:
            return None

        # CRC-16/CCITT-FALSE over the complete 33-byte frame (residual must be 0)
        if crc16(msg, poly=0x1021, init=0xD636, ref_in=False, ref_out=False) != 0:
            return None

        # IDs are little-endian 32-bit values
        target_id = (msg[3] << 24) | (msg[2] << 16) | (msg[1] << 8) | msg[0]
        source_id = (msg[7] << 24) | (msg[6] << 16) | (msg[5] << 8) | msg[4]
        counter   = msg[8]
        msg_type  = msg[9]
        msg_len   = msg[10]

        if msg_len > 20:
            return None   # sanity: payload length field must be ≤ 20

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "target_id": f"{target_id:08x}",
            "source_id": f"{source_id:08x}",
            "counter":   counter,
            "msg_type":  f"0x{msg_type:02x}",
            "payload":   msg[11:11 + msg_len].hex(),
        })


__all__ = ["BresserGarden"]
