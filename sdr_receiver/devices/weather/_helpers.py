"""Shared helpers for weather device decoders.

Usage from a weather device file:
    from ._helpers import _find_preamble, _extract_bytes, _lfsr_digest16
"""
from ...dsp import bits_to_int
from .._helpers import (
    _add_nibbles,
    _lfsr_digest8,
    _lfsr_digest8_reflect,
    _lfsr_digest16,
    _reverse8,
    _sign16,
    _sign16_top12,
)

# Re-export cross-cutting helpers so callers only need one import line.
__all__ = [
    "_add_nibbles",
    "_extract_bytes",
    "_find_preamble",
    "_fsk_pcm_to_bits",
    "_lfsr_digest8",
    "_lfsr_digest8_reflect",
    "_lfsr_digest16",
    "_reverse8",
    "_sign16",
    "_sign16_top12",
]


def _find_preamble(bits: list, pattern: bytes) -> int:
    """Search for *pattern* (as MSB-first bits) in the bit list.

    Returns the index of the first bit AFTER the pattern, or -1 if absent.
    """
    pat: list = []
    for b in pattern:
        for i in range(7, -1, -1):
            pat.append((b >> i) & 1)
    n = len(pat)
    for i in range(len(bits) - n + 1):
        if bits[i: i + n] == pat:
            return i + n
    return -1


def _extract_bytes(bits: list, offset: int, n_bytes: int) -> "bytes | None":
    """Extract *n_bytes* big-endian bytes from *bits* starting at *offset*.

    Returns None when there are insufficient bits.
    """
    end = offset + n_bytes * 8
    if end > len(bits):
        return None
    return bytes(
        bits_to_int(bits[offset + i * 8: offset + i * 8 + 8])
        for i in range(n_bytes)
    )


def _fsk_pcm_to_bits(pulses: list, chip_us: float) -> list:
    """Convert a FSK/OOK PCM pulse-stream to a flat bit list.

    Each Pulse(pulse_us, gap_us) contributes high chips (1s) for the pulse
    period and low chips (0s) for the gap period.
    """
    bits: list = []
    for p in pulses:
        n_hi = max(1, round(p.pulse_us / chip_us))
        bits.extend([1] * n_hi)
        if p.gap_us > 0:
            n_lo = round(p.gap_us / chip_us)
            if n_lo > 0:
                bits.extend([0] * n_lo)
    return bits
