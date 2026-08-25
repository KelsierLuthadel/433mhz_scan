"""Auriol AFT 77 B2 temperature sensor."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int, checksum_sum
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _lfsr_galois(data: bytes, gen: int, key: int) -> int:
    """Galois LFSR digest-8, MSB-first bit order.
    Matches rtl_433's lsrc() / lfsr_digest8() with left-shift variant."""
    result = 0
    k = key & 0xFF
    for byte in data:
        for mask in (0x80, 0x40, 0x20, 0x10, 0x08, 0x04, 0x02, 0x01):
            if byte & mask:
                result ^= k
            if k & 0x01:
                k = (k >> 1) ^ gen
            else:
                k >>= 1
    return result & 0xFF


class AuriolAFT77B2(OOKPPMDecoder):
    """Auriol AFT 77 B2 temperature sensor."""
    name     = "Auriol-AFT77B2"
    short_us = 500.0
    long_us  = 920.0
    reset_us = 2_275.0
    n_bits   = 68

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 68:
            return None

        # Extract 8 full bytes + 4-bit nibble (the 9th partial byte)
        ptr = [bits_to_int(bits[i:i + 8]) for i in range(0, 64, 8)]  # ptr[0..7]
        last4 = bits_to_int(bits[64:68])
        ptr.append(last4 << 4)  # ptr[8]  upper nibble only

        # Preamble check
        if ptr[0] != 0xA5:
            return None

        # Build 8-byte frame by nibble-shifting left by 4
        frame = bytes(((ptr[i] << 4) | (ptr[i + 1] >> 4)) & 0xFF for i in range(8))

        # Additive checksum over frame[0:6]
        if checksum_sum(frame[:6], 0xFF) != frame[6]:
            return None

        # Galois LFSR check (bit-order per rtl_433 lsrc: LSB feedback, MSB scan)
        if _lfsr_galois(frame[:6], gen=0x83, key=0xEC) != frame[7]:
            return None

        device_id = frame[1]

        # Temperature uses raw ptr bytes (ptr = b[] in C source)
        temp_raw = (ptr[4] >> 4) * 100 + (ptr[4] & 0x0F) * 10 + (ptr[5] >> 4)
        if ptr[3] & 0x08:
            temp_raw = -temp_raw
        temp_c = temp_raw * 0.1

        if not -50.0 <= temp_c <= 80.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "temperature_C": round(temp_c, 2),
        })


__all__ = ["AuriolAFT77B2"]
