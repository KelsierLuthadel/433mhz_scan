"""iMars T240 TPMS sensor.

iMars T240 TPMS decoder.

OOK_PULSE_PCM chip=50 µs.
32-bit preamble 0xaaaaaaaa then 128 raw chips -> Manchester decode -> 8 bytes.
Validation:
  B7 == B0
  (B0 & 0x0f) == (B1 & 0x0f)
  (B3 + B4) & 0xff in {0x41, 0x3c}
Fields: hexadecimal code string (B0-B6).

Source: tpms_imars_t240.c
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _manchester_decode, _bits_to_bytes_n
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsImarsT240(OOKPCMDecoder):
    """iMars T240 TPMS sensor."""

    name     = "iMars-T240"
    chip_us  = 50.0
    reset_us = 200.0
    n_bits   = 160  # 32 preamble + 128 data chips

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Find 32-bit preamble 0xaaaaaaaa = 32 alternating chips 1,0,1,0,...
        preamble = [1, 0] * 16
        pos = -1
        for i in range(len(bits) - 160 + 1):
            if bits[i: i + 32] == preamble:
                pos = i + 32
                break
        if pos < 0 or pos + 128 > len(bits):
            return None

        data_bits = _manchester_decode(bits[pos: pos + 128])
        if data_bits is None or len(data_bits) < 64:
            return None

        b = _bits_to_bytes_n(data_bits, 8)
        if b is None:
            return None

        if b[7] != b[0]:
            return None
        if (b[0] & 0x0F) != (b[1] & 0x0F):
            return None
        checksum = (b[3] + b[4]) & 0xFF
        if checksum not in (0x41, 0x3C):
            return None

        code = b[:7].hex().upper()
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "code": code,
            "mic":  "CHECKSUM",
        })


__all__ = ["TpmsImarsT240"]
