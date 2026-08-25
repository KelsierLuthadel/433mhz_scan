"""FT-004-B wireless pool/spa thermometer."""
from __future__ import annotations
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


class FT004B(OOKPPMDecoder):
    """FT-004-B wireless pool/spa thermometer.

    Modulation: OOK_PULSE_PPM
    short_us=1956 (gap=0), long_us=3900 (gap=1), reset_us=4000
    Transmits 3 × 46-bit frames consecutively (~138 bits per row).
    The C decoder reverses bit order within each byte (LSB-first transmission),
    then validates type code 0xF4 at byte 0.
    Temperature: 11-bit raw = (byte4 bits[2:0] << 8) | byte3; temp_C = raw * 0.05 - 40.
    No checksum.
    """

    name = "FT-004B"
    short_us = 1956.0
    long_us = 3900.0
    reset_us = 4000.0
    n_bits = 138  # 3 × 46 bits transmitted together; use first 46 bits

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 46:
            return None

        # Transmission is LSB-first; reverse each byte to get standard byte values.
        def rev_byte(b: list[int]) -> list[int]:
            return list(reversed(b))

        b0 = rev_byte(bits[0:8])
        if bits_to_int(b0) != 0xF4:
            return None

        # Temperature: byte3 is LSB, bits 0-2 of byte4 are MSB (3 bits = upper bits)
        # "bits 0-2 of byte4" in C convention (bit0=LSB) = 3 LSBs of original byte.
        # After LSB-first reversal: b4_rev[5:8] = original bits 2:0 reversed → [bit2,bit1,bit0]
        b3 = rev_byte(bits[24:32])
        b4 = rev_byte(bits[32:40])
        # Original bits 0-2 (3 LSBs of byte4) are at indices 5,6,7 of b4 (after LSB→MSB reversal)
        temp_msb = bits_to_int(b4[5:8])  # 3 bits → upper part of 11-bit value
        temp_lsb = bits_to_int(b3)       # 8 bits → lower part
        temp_raw = (temp_msb << 8) | temp_lsb
        temp_c = temp_raw * 0.05 - 40.0
        if not -40.0 <= temp_c <= 125.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["FT004B"]
