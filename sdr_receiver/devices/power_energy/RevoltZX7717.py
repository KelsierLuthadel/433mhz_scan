"""@file
    Revolt ZX-7717-675 433 MHz power meter.

    Copyright (C) 2024 Christian W. Zuckschwerdt <zany@triq.net>
    Copyright (C) 2024 Boing <dhs_mobil@google.com>

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

Revolt ZX-7717-675 433 MHz power meter.

- Used with Revolt ZX-7716 Monitor.
- Other names: HPM-27717, ZX-7717-919
- Up to 6 channels
- First seen: 12-2024
- https://www.revolt-power.de/TOP-KAT161-Zusaetzliche-Steckdose-ZX-7717-919.shtml

Outputs are: Current (A) max 15.999 A, Voltage (V) max 250.0 V,
Power (VA) max 3679.9 VA, PF (calculated), 8 bit checksum.

Modulation: ASK/OOK with Manchester coding.
Send interval: 5 secs and/or when current changes.

The packet is 14 manchester encoded bytes with a Preamble of 0x2A and
an 8-bit checksum (last byte).
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class RevoltZX7717(ManchesterDecoder):
    """Revolt ZX-7717 wireless power socket meter.

    Modulation: OOK_PULSE_MANCHESTER_ZEROBIT, chip 310 µs.
    Frame starts with preamble 0x2A, then a length byte:
        0x0D / 0x0E  power message (13/14 bytes of payload)
        0x11 / 0x12  energy message (17/18 bytes of payload)

    Power message (relative to preamble byte at index 0):
        [0]   0x2A preamble
        [1]   length (0x0D = 13)
        [2-3] device ID (little-endian)
        [4]   version
        [5]   flags
        [6]   type/unknown
        [7]   unknown
        [8-9] current (mA, little-endian)
        [10-11] voltage (×0.1 V, little-endian)
        [12-13] power (×0.1 W, little-endian)
        [14]  checksum = sum(bytes 0-13) mod 256

    Checksum: sum of all frame bytes except last == last byte, mod 256.
    """
    name      = "Revolt-ZX7717"
    chip_us   = 310.0
    reset_us  = 900.0
    n_bits    = 120       # 15 bytes minimum (preamble + length + 13 data)
    inverted  = False

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        n_bytes = len(bits) // 8
        if n_bytes < 15:
            return None
        b = [bits_to_int(bits[i:i + 8]) for i in range(0, n_bytes * 8, 8)]
        # Locate preamble 0x2A
        start = -1
        for i in range(min(5, n_bytes)):
            if b[i] == 0x2A:
                start = i
                break
        if start < 0:
            return None
        msg = b[start:]
        if len(msg) < 15:
            return None
        length = msg[1]
        if length not in (0x0D, 0x0E, 0x11, 0x12):
            return None
        total = 2 + length          # preamble + length_byte + `length` data bytes
        if len(msg) < total:
            return None
        frame = msg[:total]
        if sum(frame[:-1]) & 0xFF != frame[-1]:
            return None
        device_id = msg[2] | (msg[3] << 8)
        version   = msg[4]
        if length in (0x0D, 0x0E):  # power message
            current_a = (msg[8]  | (msg[9]  << 8)) * 0.001
            voltage_v = (msg[10] | (msg[11] << 8)) * 0.1
            power_w   = (msg[12] | (msg[13] << 8)) * 0.1
            return DecodedPacket.from_fields(self.name, freq_hz, {
                "id":        device_id,
                "version":   version,
                "current_A": round(current_a, 3),
                "voltage_V": round(voltage_v, 1),
                "power_W":   round(power_w, 1),
                "mic":       "CHECKSUM",
            })
        # Energy messages need more bytes than the minimum n_bits window; partial only.
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":      device_id,
            "version": version,
            "mic":     "CHECKSUM",
        })


__all__ = ["RevoltZX7717"]
