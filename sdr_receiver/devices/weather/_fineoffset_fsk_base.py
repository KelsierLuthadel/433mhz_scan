"""Shared FSK base infrastructure for Fine Offset FSK sensors."""
from __future__ import annotations
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


# Bit pattern for Fine Offset FSK sync: 0xAA 0x2D 0xD4
_FO_SYNC_BITS: list[int] = [
    1, 0, 1, 0, 1, 0, 1, 0,   # 0xAA
    0, 0, 1, 0, 1, 1, 0, 1,   # 0x2D
    1, 1, 0, 1, 0, 1, 0, 0,   # 0xD4
]


def _fo_find_payload(bits: list[int], n_bytes: int) -> bytes | None:
    """Search for the Fine Offset sync word 0xAA 0x2D 0xD4 in a raw bit
    stream and return *n_bytes* payload bytes immediately following it.
    Returns None when the sync word is not found or the payload is truncated.
    """
    target = _FO_SYNC_BITS
    tn = len(target)
    end = len(bits) - tn - n_bytes * 8
    for i in range(max(0, end + 1)):
        if bits[i : i + tn] == target:
            start = i + tn
            if start + n_bytes * 8 <= len(bits):
                return bytes(
                    bits_to_int(bits[start + j * 8 : start + j * 8 + 8])
                    for j in range(n_bytes)
                )
    return None


class _FineOffsetFSKBase(FSKPCMDecoder):
    """Common FSK base for Fine Offset sensors (preamble 0xAA 0x2D 0xD4).

    Overrides *decode_fsk* to scan the entire demodulated bit stream for the
    sync word rather than using the fixed-offset windowing of the parent.
    """
    freq_hz = 433.92e6
    n_bits  = 256  # generous placeholder; unused by our override

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        bits_arr = demodulate_fsk(samples, sample_rate, self.bit_rate)
        bits = [int(b) for b in bits_arr]
        return self._parse(bits, self.freq_hz)


__all__: list[str] = []  # private, not exported
