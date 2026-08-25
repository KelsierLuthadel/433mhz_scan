"""Elero bidirectional 868/915 MHz blinds/awning remote protocol.

Copyright (C) 2026 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Elero bidirectional 868/915 MHz blinds/awning remote protocol.

Used by Elero-based blinds/awning/curtain motor remotes, e.g. the
Silent Gliss 5600/11490-series wall switch. Reverse engineered in
issue #3083 (https://github.com/merbanan/rtl_433/issues/3083), from
real captures and cross-checked against the independent
QuadCorei8085/elero_protocol and andyboeh/esphome-elero projects.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class Elero(RawDecoder):
    """Elero motorised-blind remote.

    FSK_PULSE_PCM, chip=13 µs, reset=4000 µs.
    Sync: 0xa723a723 (32 bits).  Payload whitened; CRC-16/IBM (poly=0x8005,
    init=0xffff).  8-byte encrypted command block + 24-bit address.
    Stub: FSK demodulation not supported in OOK pipeline.
    """
    name = "Elero"

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        return None   # requires FSK demodulation


__all__ = ["Elero"]
