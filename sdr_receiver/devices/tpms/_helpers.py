"""Shared helpers for TPMS device decoders.

Usage from a tpms device file:
    from ._helpers import _bits_to_bytes, _bits_to_bytes_n, _pulses_to_chips
"""
from .._helpers import (
    _bits_to_bytes,
    _bits_to_bytes_n,
    _reverse8,
)

__all__ = [
    "_bits_to_bytes",
    "_bits_to_bytes_n",
    "_diff_manchester_decode",
    "_find_pattern",
    "_int_to_bits",
    "_manchester_decode",
    "_mc_decode",
    "_pulses_to_chips",
    "_reverse8",
    "_xor_bytes",
]


def _pulses_to_chips(pulses, chip_us: float, tol: float = 0.45) -> list:
    """Convert a pulse list to a binary chip array for PCM/FSK-PCM signals."""
    chips = []
    for p in pulses:
        pw = getattr(p, "pulse", None) or getattr(p, "duration", 0)
        gw = getattr(p, "gap", 0)
        if chip_us > 0:
            n_hi = max(0, round(pw / chip_us))
        else:
            n_hi = 1 if pw > 0 else 0
        chips.extend([1] * n_hi)
        if gw and gw < chip_us * 50:
            n_lo = max(0, round(gw / chip_us))
            chips.extend([0] * n_lo)
    return chips


def _manchester_decode(chips: list) -> "list | None":
    """Decode Manchester chips (01→0, 10→1). Returns list or None on error."""
    bits = []
    i = 0
    while i + 1 < len(chips):
        a, b = chips[i], chips[i + 1]
        if a == 0 and b == 1:
            bits.append(0)
        elif a == 1 and b == 0:
            bits.append(1)
        else:
            return bits if len(bits) >= 8 else None
        i += 2
    return bits


def _diff_manchester_decode(chips: list, init: int = 1) -> list:
    """Differential Manchester decode (transition at start → 0, no transition → 1)."""
    bits = []
    prev = init
    i = 0
    while i + 1 < len(chips):
        curr = chips[i]
        bits.append(0 if curr != prev else 1)
        prev = chips[i + 1]
        i += 2
    return bits


def _find_pattern(chips: list, pattern: list) -> int:
    """Return the index of the first occurrence of *pattern* in *chips*, or -1."""
    pl = len(pattern)
    for i in range(len(chips) - pl + 1):
        if chips[i: i + pl] == pattern:
            return i
    return -1


def _mc_decode(chips: list, max_bits: int = 0) -> list:
    """Manchester (G.E. Thomas) decode: chip pair (0,1)->0, (1,0)->1.

    Stops silently on the first invalid chip pair.  Optionally limits output
    to *max_bits* bits (processes at most ``max_bits * 2`` chips).
    """
    out: list = []
    limit = len(chips) & ~1
    if max_bits:
        limit = min(limit, max_bits * 2)
    i = 0
    while i + 1 < limit:
        a, b = chips[i], chips[i + 1]
        if a == 0 and b == 1:
            out.append(0)
        elif a == 1 and b == 0:
            out.append(1)
        else:
            break
        i += 2
    return out


def _int_to_bits(value: int, width: int) -> list:
    """Return *value* as an MSB-first bit list of exactly *width* bits."""
    return [(value >> (width - 1 - i)) & 1 for i in range(width)]


def _xor_bytes(data: bytes) -> int:
    """XOR-reduce all bytes in *data* and return the result."""
    result = 0
    for b in data:
        result ^= b
    return result
