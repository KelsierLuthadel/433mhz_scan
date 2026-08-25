"""Shared private helper functions used across device decoders.

Import only what you need:
    from .._helpers import _bits_to_bytes, _reverse8
    from ._helpers import _bits_to_bytes        # from within devices/
"""
from ..dsp import bits_to_int


# ---------------------------------------------------------------------------
# Bit packing
# ---------------------------------------------------------------------------

def _bits_to_bytes(bits: list) -> bytes:
    """Pack MSB-first bit list into bytes, truncating trailing partial byte."""
    return bytes(bits_to_int(bits[i: i + 8]) for i in range(0, len(bits) - 7, 8))


def _bits_to_bytes_n(bits: list, n_bytes: int) -> "bytes | None":
    """Pack first n_bytes * 8 MSB-first bits into bytes; None if too short."""
    if len(bits) < n_bytes * 8:
        return None
    return bytes(bits_to_int(bits[i * 8: i * 8 + 8]) for i in range(n_bytes))


def _bits_to_bytes_lsb(bits: list) -> list:
    """Pack bits LSB-first into bytes (bit[0] = LSB of byte 0)."""
    result: list = []
    for i in range(0, len(bits), 8):
        chunk = bits[i: i + 8]
        result.append(sum(b << j for j, b in enumerate(chunk)) & 0xFF)
    return result


# ---------------------------------------------------------------------------
# Byte-level bit reversal
# ---------------------------------------------------------------------------

def _reverse8(b: int) -> int:
    """Reverse the bit order of a single byte (rtl_433 reflect8)."""
    b = ((b & 0xF0) >> 4) | ((b & 0x0F) << 4)
    b = ((b & 0xCC) >> 2) | ((b & 0x33) << 2)
    b = ((b & 0xAA) >> 1) | ((b & 0x55) << 1)
    return b & 0xFF


# ---------------------------------------------------------------------------
# Checksums / CRCs
# ---------------------------------------------------------------------------

def _crc4(data: bytes, poly: int = 0x3, init: int = 0x0) -> int:
    """4-bit CRC, MSB-first (rtl_433 crc4 convention)."""
    crc = init & 0xF
    for byte in data:
        for i in range(7, -1, -1):
            bit = (byte >> i) & 1
            if ((crc >> 3) & 1) ^ bit:
                crc = ((crc << 1) & 0xF) ^ poly
            else:
                crc = (crc << 1) & 0xF
    return crc


def _lfsr_digest8(data: bytes, gen: int, key: int) -> int:
    """LFSR-based 8-bit digest (rtl_433 lfsr_digest8)."""
    s = 0
    for byte in data:
        for i in range(7, -1, -1):
            if (byte >> i) & 1:
                s ^= key
            key = (key >> 1) ^ gen if (key & 1) else key >> 1
    return s


def _lfsr_digest16(data: bytes, gen: int, key: int) -> int:
    """LFSR-16 keyed digest (rtl_433 lfsr_digest16).

    For each bit (MSB-first) of every byte in *data*:
      - If the bit is 1, XOR the running sum with *key*.
      - Advance *key*: if key LSB is 1 → (key >> 1) ^ gen, else key >> 1.
    """
    s = 0
    for byte in data:
        for i in range(7, -1, -1):
            if (byte >> i) & 1:
                s ^= key
            if key & 1:
                key = (key >> 1) ^ gen
            else:
                key >>= 1
    return s & 0xFFFF


def _lfsr_digest8_reflect(data: "bytes | bytearray", n: int, gen: int, key: int) -> int:
    """Galois LFSR digest with byte reflection (rtl_433 lfsr_digest8_reflect).

    Processes *n* bytes from *data* in reverse order, reflecting each byte,
    then returns reflect8(final_key).
    """
    key &= 0xFF
    for k in range(n - 1, -1, -1):
        d = _reverse8(data[k])
        for i in range(7, -1, -1):
            if ((d >> i) & 1) ^ ((key >> 7) & 1):
                key ^= gen
            key = (key << 1) & 0xFF
    return _reverse8(key)


# ---------------------------------------------------------------------------
# Sign-extension helpers (used by temperature sensors)
# ---------------------------------------------------------------------------

def _sign16(raw: int) -> int:
    """Sign-extend a 16-bit unsigned value to a signed int."""
    return raw - 0x10000 if raw >= 0x8000 else raw


def _sign16_top12(t16: int) -> int:
    """Take a value packed in the top 12 bits of a 16-bit word and sign-extend."""
    if t16 >= 0x8000:
        t16 -= 0x10000
    return t16 >> 4


# ---------------------------------------------------------------------------
# Nibble / byte accumulation
# ---------------------------------------------------------------------------

def _add_nibbles(data: bytes) -> int:
    """Sum all nibbles in *data*."""
    s = 0
    for byte in data:
        s += (byte >> 4) + (byte & 0x0F)
    return s
