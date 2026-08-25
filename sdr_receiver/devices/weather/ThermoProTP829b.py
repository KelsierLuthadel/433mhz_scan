"""ThermoPro TP829B / TP829 4-Probe Meat Thermometer (FSK PCM 102 µs)."""
from __future__ import annotations
from ..base import RawDecoder
from ._helpers import _fsk_pcm_to_bits, _find_preamble, _extract_bytes, _lfsr_digest8
from ...packet import DecodedPacket


class ThermoProTP829b(RawDecoder):
    """ThermoPro TP829B / TP829 4-Probe Meat Thermometer (FSK PCM 102 µs).

    Preamble: 0x55 0x2D 0xD4 (24 bits).
    Payload: 9 bytes  id[8] | unit+flags[8] | 4×12-bit-temp | checksum[8].
    Checksum: Galois LFSR over byte-reversed payload[0:8], gen=0x98, key=0x55.
    temp_C = (raw - 500) * 0.1;  raw==0xEDD means probe absent.
    Conflict guard: bytes[5:8] == 0xAA 0x55 0xAA && cksum==0 → TX7B, skip.
    """

    _CHIP_US  = 102.0
    _PREAMBLE = bytes([0x55, 0x2D, 0xD4])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        bits   = _fsk_pcm_to_bits(pulses, self._CHIP_US)
        offset = _find_preamble(bits, self._PREAMBLE)
        if offset < 0 or (len(bits) - offset) < 72:
            return None
        b = _extract_bytes(bits, offset, 9)
        # Exclude conflict with TX7B
        if b[5] == 0xAA and b[6] == 0x55 and b[7] == 0xAA and b[8] == 0:
            return None
        # Galois LFSR: byte-reverse first 8 bytes, gen=0x98, key=0x55
        if _lfsr_digest8(bytes(reversed(b[:8])), 0x98, 0x55) != b[8]:
            return None

        id_       = b[0]
        display_u = (b[1] & 0xF0) >> 4
        flags     = b[1] & 0xF
        p1_raw    = (b[2] << 4) | ((b[3] & 0xF0) >> 4)
        p2_raw    = ((b[3] & 0x0F) << 8) | b[4]
        p3_raw    = (b[5] << 4) | ((b[6] & 0xF0) >> 4)
        p4_raw    = ((b[6] & 0x0F) << 8) | b[7]

        fields: dict = {
            "id":           f"{id_:02x}",
            "display_unit": "Fahrenheit" if display_u == 0x2 else "Celsius",
            "flags":        f"{flags:01x}",
        }
        for idx, raw in enumerate([p1_raw, p2_raw, p3_raw, p4_raw], 1):
            if raw != 0xEDD:
                fields[f"temperature_{idx}_C"] = round((raw - 500) * 0.1, 1)
        return DecodedPacket.from_fields("ThermoPro-TP829b", freq_hz, fields)


__all__ = ["ThermoProTP829b"]
