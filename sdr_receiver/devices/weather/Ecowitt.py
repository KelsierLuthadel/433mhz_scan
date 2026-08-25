"""Ecowitt WH53 / WH0280 / WH0281A wireless outdoor thermometer."""
from __future__ import annotations
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket


class Ecowitt(OOKPWMDecoder):
    """Ecowitt WH53 / WH0280 / WH0281A wireless outdoor thermometer."""
    name     = "Ecowitt-WH53"
    short_us = 500.0
    long_us  = 1_480.0
    reset_us = 4_000.0
    n_bits   = 55

    # 12-bit preamble: first 12 bits of {0xF5, 0x30}
    # 0xF5 = 1111 0101,  0x30 = 0011 0000  → first 12 bits = 1111 0101 0011
    _PREAMBLE_12 = [1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 1, 1]

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # Locate the 12-bit preamble; payload follows immediately after.
        preamble = self._PREAMBLE_12
        data_start = -1
        for i in range(max(1, len(bits) - 54)):
            if bits[i:i + 12] == preamble:
                data_start = i + 12
                break
        if data_start < 0:
            # Fallback: assume bits start with payload (preamble already stripped)
            data_start = 0

        payload = bits[data_start:]
        if len(payload) < 43:
            return None

        # 43-bit payload: [7-bit header][8-bit model][8-bit ID][2-bit ch][10-bit temp][8-bit CRC]
        # header = payload[0:7]   typically a sync/marker, not decoded
        model_byte = bits_to_int(payload[7:15])
        if model_byte != 0x53:
            return None

        sensor_id = bits_to_int(payload[15:23])
        ch_raw    = bits_to_int(payload[23:25])
        channel   = ch_raw + 1                    # 0-indexed → 1-indexed (1–3)
        temp_raw  = bits_to_int(payload[25:35])
        crc_recv  = bits_to_int(payload[35:43])

        # CRC-8 (poly=0x31, init=0x00) over the four bytes preceding the CRC.
        # Pack model + ID + (ch<<6 | temp[9:4]) + (temp[3:0]<<4) into bytes.
        byte2 = (ch_raw << 6) | (temp_raw >> 4)
        byte3 = (temp_raw & 0x0F) << 4
        chk_data = bytes([model_byte, sensor_id, byte2 & 0xFF, byte3 & 0xFF])
        if crc8(chk_data, poly=0x31, init=0x00) != crc_recv:
            return None

        temp_c = temp_raw * 0.1 - 40.0
        if not -40.0 <= temp_c <= 60.0:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "temperature_C": round(temp_c, 1),
        })


__all__ = ["Ecowitt"]
