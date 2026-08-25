"""Citroen FSK 10 byte Manchester encoded checksummed TPMS data.

Copyright (C) 2017 Christian W. Zuckschwerdt <zany@triq.net>

Citroen TPMS decoder (also Peugeot, Fiat, Mitsubishi, VDO-types).

The decoder processes tire pressure monitoring signals from Citroen vehicles.
Packet structure includes: state, 32-bit sensor ID, flags, repeat counter,
pressure reading (in 1.364 kPa increments), temperature (Celsius offset by 50),
battery status indicator, and XOR checksum validation across bytes 1-9.

Source: tpms_citroen.c
Modulation: FSK_PULSE_PCM, chip=52 us
Manchester decode, 80+ bits (10 bytes)
Checksum: XOR bytes 1-9 = 0 (byte 0 excluded)
Pressure = byte * 1.364 kPa; Temperature = byte - 50 deg C
Layout: UU IIIIIIII FR PP TT BB CC
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
from ._helpers import _mc_decode, _bits_to_bytes, _xor_bytes
if TYPE_CHECKING:
    from ...dsp import Pulse


class TPMSCitroen(FSKPCMDecoder):
    """Citroen TPMS  FSK/Manchester, XOR checksum."""

    name     = "Citroen-TPMS"
    bit_rate = 1_000_000.0 / 52
    n_bits   = 200
    freq_hz  = 433.92e6

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ...dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        return self._decode_bits([int(x) for x in raw])

    def _decode_bits(self, chips: list[int]) -> DecodedPacket | None:
        # Search for start of valid Manchester region (try multiple offsets)
        for offset in range(min(32, len(chips))):
            decoded = _mc_decode(chips[offset:], 88)
            if len(decoded) < 80:
                continue
            b = _bits_to_bytes(decoded[:80])
            if len(b) < 10:
                continue
            if b[6] == 0 or b[7] == 0:
                continue
            # XOR checksum: bytes 1..9 must XOR to 0
            if _xor_bytes(b[1:10]) != 0:
                continue

            state   = b[0]
            sid     = (b[1] << 24) | (b[2] << 16) | (b[3] << 8) | b[4]
            flags   = b[5] >> 4
            repeat  = b[5] & 0x0F
            pres    = round(b[6] * 1.364, 0)
            temp    = b[7] - 50
            batt    = b[8]

            state_str = {0x00: "OK", 0x01: "Alert"}.get(state, f"0x{state:02x}")
            return DecodedPacket.from_fields("Citroen-TPMS", self.freq_hz, {
                "id":            f"{sid:08x}",
                "state":         state_str,
                "flags":         flags,
                "repeat":        repeat,
                "pressure_kPa":  pres,
                "temperature_C": temp,
                "maybe_battery": batt,
            })
        return None

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        return self._decode_bits(bits)


__all__ = ["TPMSCitroen"]
