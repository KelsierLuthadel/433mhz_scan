"""ThermoPro TP828B 2-Probe Meat Thermometer (FSK PCM 102 µs)."""
from __future__ import annotations
from ..base import RawDecoder
from ._helpers import _fsk_pcm_to_bits, _find_preamble, _extract_bytes, _lfsr_digest8
from ...packet import DecodedPacket


class ThermoProTP828b(RawDecoder):
    """ThermoPro TP828B 2-Probe Meat Thermometer (FSK PCM 102 µs).

    Preamble: 0x55 0x2D 0xD4 (24 bits).
    Payload: 12 bytes  id[8] | unit+flags[8] | 5×12-bit-temp | checksum[8].
    Checksum: Galois LFSR over byte-reversed payload[0:11], gen=0x98,
              key=0x16, XOR 0xAC; result in byte 11.
    temp_C = (raw - 500) * 0.1;  raw==0xEDD means probe absent.
    """

    _CHIP_US  = 102.0
    _PREAMBLE = bytes([0x55, 0x2D, 0xD4])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        bits   = _fsk_pcm_to_bits(pulses, self._CHIP_US)
        offset = _find_preamble(bits, self._PREAMBLE)
        if offset < 0 or (len(bits) - offset) < 96:
            return None
        b = _extract_bytes(bits, offset, 12)
        # Galois LFSR: byte-reverse first 11 bytes, gen=0x98, key=0x16, XOR 0xAC
        if (_lfsr_digest8(bytes(reversed(b[:11])), 0x98, 0x16) ^ 0xAC) != b[11]:
            return None

        id_       = b[0]
        display_u = (b[1] & 0xF0) >> 4
        flags     = b[1] & 0xF
        p1_raw    = (b[2] << 4) | ((b[3] & 0xF0) >> 4)
        p1_lo_raw = ((b[3] & 0x0F) << 8) | b[4]
        p1_hi_raw = (b[5] << 4) | ((b[6] & 0xF0) >> 4)
        p2_raw    = ((b[6] & 0x0F) << 8) | b[7]
        p2_lo_raw = (b[8] << 4) | ((b[9] & 0xF0) >> 4)
        p2_hi_raw = ((b[9] & 0x0F) << 8) | b[10]

        fields: dict = {
            "id":           f"{id_:02x}",
            "display_unit": "Fahrenheit" if display_u == 0x2 else "Celsius",
            "flags":        f"{flags:01x}",
        }
        if p1_raw != 0xEDD:
            fields["temperature_1_C"]    = round((p1_raw - 500) * 0.1, 1)
        if p1_lo_raw != 0xEAA:
            fields["temperature_1_LO_C"] = round((p1_lo_raw - 500) * 0.1, 1)
        fields["temperature_1_HI_C"]     = round((p1_hi_raw - 500) * 0.1, 1)
        if p2_raw != 0xEDD:
            fields["temperature_2_C"]    = round((p2_raw - 500) * 0.1, 1)
        if p2_lo_raw != 0xEAA:
            fields["temperature_2_LO_C"] = round((p2_lo_raw - 500) * 0.1, 1)
        fields["temperature_2_HI_C"]     = round((p2_hi_raw - 500) * 0.1, 1)
        return DecodedPacket.from_fields("ThermoPro-TP828b", freq_hz, fields)


__all__ = ["ThermoProTP828b"]
