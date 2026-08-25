"""ThermoPro TP211B Thermometer (FSK PCM 105 µs, 915 MHz)."""
from __future__ import annotations
from ..base import RawDecoder
from ._helpers import _fsk_pcm_to_bits, _find_preamble, _extract_bytes
from ...packet import DecodedPacket


# TP211B XOR-table checksum (48 entries, one per bit of the 6-byte payload)
_TP211B_XOR_TABLE = [
    0xC881, 0xC441, 0xC221, 0xC111, 0xC089, 0xC045, 0xC023, 0xC010,
    0xC01F, 0xC00E, 0x6007, 0x9002, 0x4801, 0x8401, 0xE201, 0xD101,
    0xDE01, 0xCF01, 0xC781, 0xC3C1, 0xC1E1, 0xC0F1, 0xC079, 0xC03D,
    0xC029, 0xC015, 0xC00B, 0xC004, 0x6002, 0x3001, 0xB801, 0xFC01,
    0xE801, 0xD401, 0xCA01, 0xC501, 0xC281, 0xC141, 0xC0A1, 0xC051,
    0xC061, 0xC031, 0xC019, 0xC00D, 0xC007, 0xC002, 0x6001, 0x9001,
]


def _tp211b_checksum(b: bytes) -> int:
    """ThermoPro TP211B XOR-table checksum over first 6 data bytes."""
    checksum = 0x411B
    for n in range(6):
        for i in range(8):
            # (b[n] << (i+1)) & 0x100 tests bit (7-i) of b[n], MSB first
            if (b[n] << (i + 1)) & 0x100:
                checksum ^= _TP211B_XOR_TABLE[n * 8 + i]
    return checksum & 0xFFFF


class ThermoProTP211B(RawDecoder):
    """ThermoPro TP211B Thermometer (FSK PCM 105 µs, 915 MHz).

    Preamble: 0x55 0x2D 0xD4 (24 bits).
    Payload: 8 bytes  Sensor-ID[24] | bat+temp[16] | 0xAA | checksum[16].
    Checksum: XOR-table over 6 bytes, seed 0x411B, result in bytes 6–7.
    temp_C = (raw - 500) * 0.1
    """

    _CHIP_US  = 105.0
    _PREAMBLE = bytes([0x55, 0x2D, 0xD4])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        bits   = _fsk_pcm_to_bits(pulses, self._CHIP_US)
        offset = _find_preamble(bits, self._PREAMBLE)
        if offset < 0 or (len(bits) - offset) < 64:
            return None
        b = _extract_bytes(bits, offset, 8)
        if b[5] != 0xAA:
            return None
        if (not any(b[:5])) or all(x == 0xFF for x in b[:5]):
            return None
        if _tp211b_checksum(b) != ((b[6] << 8) | b[7]):
            return None
        sensor_id = (b[0] << 16) | (b[1] << 8) | b[2]
        temp_raw  = ((b[3] & 0x0F) << 8) | b[4]
        temp_c    = (temp_raw - 500) * 0.1
        low_bat   = (b[3] & 0x80) >> 7
        return DecodedPacket.from_fields("ThermoPro-TP211B", freq_hz, {
            "id": f"{sensor_id:06x}",
            "battery_ok": int(not low_bat),
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["ThermoProTP211B"]
