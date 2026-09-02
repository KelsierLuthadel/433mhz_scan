"""Sensor Systems Sonic Smart oil tank level monitor.

FSK with Manchester encoding: chip=500µs, preamble=0x55 0x58, 9-byte payload.
CRC-8/MAXIM (poly=0x31, reflected) over bytes 0-7; result in byte 8.

Payload layout:
  bytes[0:4]  sensor ID (32-bit big-endian)
  byte [4]    status flags (0x80 = normal transmission)
  byte [5]    raw temperature proxy (temp_C ≈ maybetemp + 3)
  byte [6]    binding countdown when >0; depth MSB otherwise
  byte [7]    depth LSB  →  depth_cm = (byte6 << 8) | byte7
  byte [8]    CRC-8/MAXIM
"""
from __future__ import annotations

from ..base import FSKManchesterDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket


class OilSonicSmart(FSKManchesterDecoder):
    name     = "Oil-SonicSmart"
    freq_hz  = 433.92e6
    bit_rate = 2_000.0   # 500 µs chips
    n_bits   = 88        # 16-bit preamble (0x55 0x58) + 72-bit payload (9 bytes)
    inverted = False

    _PRE = [0, 1, 0, 1, 0, 1, 0, 1,   # 0x55
            0, 1, 0, 1, 1, 0, 0, 0]   # 0x58

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if bits[:16] != self._PRE:
            return None
        payload_bits = bits[16:]  # 72 bits = 9 bytes
        raw = bytes(bits_to_int(payload_bits[i : i + 8]) for i in range(0, 72, 8))
        if crc8(raw[:8], poly=0x31, init=0x00, reflected=True) != raw[8]:
            return None
        sensor_id        = int.from_bytes(raw[0:4], "big")
        flags            = raw[4]
        maybetemp        = raw[5]
        byte6            = raw[6]
        byte7            = raw[7]
        return DecodedPacket(
            model=self.name,
            raw={
                "id":                format(sensor_id, "08x"),
                "flags":             format(flags, "02x"),
                "maybetemp":         maybetemp,
                "temperature_C":     float(maybetemp + 3),
                "binding_countdown": byte6,
                "depth_cm":          (byte6 << 8) | byte7,
            },
            freq_hz=freq_hz,
        )


__all__ = ["OilSonicSmart"]
