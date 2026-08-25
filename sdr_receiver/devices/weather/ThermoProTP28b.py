"""ThermoPro TP28b BBQ Meat Thermometer (FSK PCM 105 µs, dual probe)."""
from __future__ import annotations
from ..base import RawDecoder
from ._helpers import _fsk_pcm_to_bits, _find_preamble, _extract_bytes
from ...packet import DecodedPacket


class ThermoProTP28b(RawDecoder):
    """ThermoPro TP28b BBQ Meat Thermometer (FSK PCM 105 µs, dual probe).

    Preamble: 0xD2 0xAA 0x2D 0xD4 (32 bits).
    Payload: 18 bytes  6×BCD-temp | flags[16] | id[16] | checksum[8] | padding.
    Checksum: sum of first 16 bytes & 0xFF equals byte 16.
    Temperatures are little-endian 16-bit BCD (LL HH).
    """

    _CHIP_US  = 105.0
    _PREAMBLE = bytes([0xD2, 0xAA, 0x2D, 0xD4])

    @staticmethod
    def _bcd2float(lo: int, hi: int) -> float:
        return (
            ((hi & 0xF0) >> 4) * 100.0
            + (hi & 0x0F) * 10.0
            + ((lo & 0xF0) >> 4) * 1.0
            + (lo & 0x0F) * 0.1
        )

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        bits   = _fsk_pcm_to_bits(pulses, self._CHIP_US)
        offset = _find_preamble(bits, self._PREAMBLE)
        if offset < 0 or (len(bits) - offset) < 144:
            return None
        b = _extract_bytes(bits, offset, 18)
        if (sum(b[:16]) & 0xFF) != b[16]:
            return None
        bcd = self._bcd2float
        id_   = (b[14] << 8) | b[15]
        flags = (b[12] << 8) | b[13]
        return DecodedPacket.from_fields("ThermoPro-TP28b", freq_hz, {
            "id":              f"{id_:04x}",
            "temperature_1_C": round(bcd(b[0],  b[1]),  1),
            "alarm_high_1_C":  round(bcd(b[2],  b[3]),  1),
            "alarm_low_1_C":   round(bcd(b[4],  b[5]),  1),
            "temperature_2_C": round(bcd(b[6],  b[7]),  1),
            "alarm_high_2_C":  round(bcd(b[8],  b[9]),  1),
            "alarm_low_2_C":   round(bcd(b[10], b[11]), 1),
            "flags":           f"{flags:04x}",
        })


__all__ = ["ThermoProTP28b"]
