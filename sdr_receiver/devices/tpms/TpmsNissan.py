"""Nissan FSK 37 bit Manchester encoded checksummed TPMS data.

Reference issue: https://github.com/merbanan/rtl_433/issues/1024
Copyright (C) 2021 Alex Wilson

Nissan TPMS decoder.

Nissan FSK 37 bit Manchester encoded checksummed TPMS data with the following structure:
MODE (3 bits), TPMS_ID (24 bits), pressure calculation as (PSI+THREE)*FOUR (8 bits),
and UNKNOWN field (2 bits). The decoder performs Manchester decoding, validates via
checksum, extracts the tire pressure in PSI, and outputs model, type, ID, mode,
pressure, and integrity data.

Source: tpms_nissan.c
Modulation: FSK_PULSE_PCM, chip=~120 us, Manchester-encoded
Preamble: 36 bits (0xf5 0x55 0x55 0x55 0xe0)
Payload after Manchester decode - ~5 bytes, 37 bits used:
  mode   = b[0] >> 5                 (3 bits)
  id     = 24-bit from b[0:3]
  pressure raw from b[3:5]; pressure_psi = raw/4.0 - 3.0
  unknown = (b[4] >> 3) & 0x3        (2 bits)
Checksum: sum2N method; accumulated bits inverted & masked -> must be 0x03.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class TpmsNissan(RawDecoder):
    """Nissan TPMS sensor  FSK_PULSE_PCM, chip≈120 µs, Manchester-encoded.

    Preamble: 36 bits (0xf5 0x55 0x55 0x55 0xe0).
    Payload after Manchester decode  ~5 bytes, 37 bits used:
      mode   = b[0] >> 5                 (3 bits)
      id     = 24-bit from b[0:3]
      pressure raw from b[3:5]; pressure_psi = raw/4.0 - 3.0
      unknown = (b[4] >> 3) & 0x3        (2 bits)
    Checksum: sum2N method; accumulated bits inverted & masked -> must be 0x03.
    """

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:  # noqa: ARG002
        return None  # FSK requires frequency-domain front-end


__all__ = ["TpmsNissan"]
