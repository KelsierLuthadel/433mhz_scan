"""ThermoPro TP-08 / TP-12 / TP-20 Dual-Probe Thermometer."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


def _reflect8(b: int) -> int:
    """Reverse the 8 bits of a byte."""
    result = 0
    for _ in range(8):
        result = (result << 1) | (b & 1)
        b >>= 1
    return result


def _lfsr_digest8_reflect(data: bytes, gen: int, key: int) -> int:
    """LFSR digest with per-byte bit reflection.

    Equivalent to rtl_433's lfsr_digest8_reflect()  each byte is
    bit-reversed before being fed into the LFSR.  Used by TP11/TP12.
    """
    s = 0
    for byte in data:
        byte = _reflect8(byte)
        for i in range(7, -1, -1):
            if (byte >> i) & 1:
                s ^= key
            if key & 1:
                key = ((key >> 1) ^ gen) & 0xFF
            else:
                key = (key >> 1) & 0xFF
    return s


class ThermoProTP12(OOKPPMDecoder):
    """ThermoPro TP-08 / TP-12 / TP-20 Dual-Probe Thermometer.

    OOK PPM, 40/41 bits.
    Integrity: LFSR-digest8-reflect (gen=0x51, key=0x04) over 4 bytes.
    Layout: id[8] | temp1_lo[8] | nibbles[8] | temp2_lo[8] | digest[8]
    where nibbles[7:4] = temp1 high, nibbles[3:0] = temp2 high.
    temp_C = (raw - 200) * 0.1
    """

    name     = "Thermopro-TP12"
    short_us = 500.0
    long_us  = 1500.0
    reset_us = 4000.0
    n_bits   = 40  # packets are 41 bits; checksum fits in first 40

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 40:
            return None
        b = bytes(bits_to_int(bits[i * 8:(i + 1) * 8]) for i in range(5))
        if not any(b[:4]):
            return None
        if _lfsr_digest8_reflect(b[:4], 0x51, 0x04) != b[4]:
            return None
        device    = b[0]
        temp1_raw = ((b[2] & 0xF0) << 4) | b[1]
        temp2_raw = ((b[2] & 0x0F) << 8) | b[3]
        temp1_c   = (temp1_raw - 200) * 0.1
        temp2_c   = (temp2_raw - 200) * 0.1
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id": device,
            "temperature_1_C": round(temp1_c, 1),
            "temperature_2_C": round(temp2_c, 1),
        })


__all__ = ["ThermoProTP12"]
