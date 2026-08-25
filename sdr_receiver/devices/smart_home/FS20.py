"""Simple FS20 remote decoder.

Copyright (C) 2019 Christian W. Zuckschwerdt <zany@triq.net>
original implementation 2019 Dominik Pusch <dominik.pusch@koeln.de>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Simple FS20 remote decoder.

Frequency: use rtl_433 -f 868.35M

fs20 protocol frame info from http://www.fhz4linux.info/tiki-index.php?page=FS20+Protocol

    preamble  hc1    parity  hc2    parity  address  parity  cmd    parity  chksum  parity  eot
    13 bit    8 bit  1 bit   8 bit  1 bit   8 bit    1 bit   8 bit  1 bit   8 bit   1 bit   1 bit

with extended commands

    preamble  hc1    parity  hc2    parity  address  parity  cmd    parity  ext    parity  chksum  parity  eot
    13 bit    8 bit  1 bit   8 bit  1 bit   8 bit    1 bit   8 bit  1 bit   8 bit  1 bit   8 bit   1 bit   1 bit

Per-byte parity and the trailing checksum byte (a Type+Hopcount residual,
restricted to the two documented Type values 6/FS20 and 0xC/FHT with a
small hopcount margin) are both checked, and command extensions are
decoded into the `ext` field.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class FS20(OOKPWMDecoder):
    """ELV FS20 / FHT home-automation system.

    OOK_PULSE_PWM, short=400 µs, long=600 µs, reset=9000 µs.
    Frame: 13-bit preamble (all-1s + 0) followed by 5 bytes each with
    8 data bits + 1 odd-parity bit = 58 bits total.
    Checksum: (HC1+HC2+Addr+Cmd+type_const) mod 256 == chk.
    type_const 6-8 → FS20, 12-14 → FHT.
    """
    name     = "FS20"
    short_us = 400.0
    long_us  = 600.0
    reset_us = 9000.0
    n_bits   = 58   # 13 preamble + 5 × 9

    @staticmethod
    def _odd_parity(val: int) -> int:
        p = 0
        for _ in range(8):
            p ^= val & 1
            val >>= 1
        return p ^ 1   # odd parity = complement of even

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 58:
            return None
        # bytes start at bit 13
        data: list[int] = []
        for i in range(5):
            base  = 13 + i * 9
            val   = bits_to_int(bits[base : base + 8])
            pbit  = bits[base + 8]
            if self._odd_parity(val) != pbit:
                return None
            data.append(val)
        hc1, hc2, addr, cmd, chk = data
        base_sum = (hc1 + hc2 + addr + cmd) & 0xFF
        # type constant adds 6-8 (FS20) or 12-14 (FHT)
        model = None
        for t in range(6, 9):
            if (base_sum + t) & 0xFF == chk:
                model = "FS20"
                break
        if model is None:
            for t in range(12, 15):
                if (base_sum + t) & 0xFF == chk:
                    model = "FHT"
                    break
        if model is None:
            return None
        return DecodedPacket.from_fields(model, freq_hz, {
            "housecode1": hc1,
            "housecode2": hc2,
            "address":    addr,
            "command":    cmd,
        })


__all__ = ["FS20"]
