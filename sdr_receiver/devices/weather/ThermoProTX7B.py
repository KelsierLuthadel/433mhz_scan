"""ThermoPro TX-7B Outdoor Thermometer / Hygrometer (FSK PCM 108 µs)."""
from __future__ import annotations
from ..base import RawDecoder
from ._helpers import _fsk_pcm_to_bits, _find_preamble, _extract_bytes, _lfsr_digest8
from ...packet import DecodedPacket


class ThermoProTX7B(RawDecoder):
    """ThermoPro TX-7B Outdoor Thermometer / Hygrometer (FSK PCM 108 µs).

    Preamble: 0x55 0x2D 0xD4 (24 bits).
    Payload: 9 bytes  id[8] | bat+btn+ch+flags[8] | temp[12] | humidity[12]
             | 0xAA 0x55 0xAA | checksum[8].
    Checksum: Galois LFSR over byte-reversed payload[0:8], gen=0x98, key=0x25.
    temp_C = (temp_raw - 400) * 0.1
    """

    _CHIP_US  = 108.0
    _PREAMBLE = bytes([0x55, 0x2D, 0xD4])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        bits   = _fsk_pcm_to_bits(pulses, self._CHIP_US)
        offset = _find_preamble(bits, self._PREAMBLE)
        if offset < 0 or (len(bits) - offset) < 72:
            return None
        b = _extract_bytes(bits, offset, 9)
        # Fixed marker bytes 5–7 must be 0xAA 0x55 0xAA
        if b[5] != 0xAA or b[6] != 0x55 or b[7] != 0xAA:
            return None
        # Galois LFSR: byte-reverse first 8 bytes, gen=0x98, key=0x25
        if _lfsr_digest8(bytes(reversed(b[:8])), 0x98, 0x25) != b[8]:
            return None

        id_       = b[0]
        low_bat   = b[1] >> 7
        tx_button = (b[1] & 0x40) >> 6
        channel   = ((b[1] & 0x30) >> 4) + 1
        flags     = b[1] & 0xF
        temp_raw  = (b[2] << 4) | ((b[3] & 0xF0) >> 4)
        humidity  = b[4]
        temp_c    = (temp_raw - 400) * 0.1

        return DecodedPacket.from_fields("ThermoPro-TX7B", freq_hz, {
            "id":            f"{id_:02x}",
            "battery_ok":    int(not low_bat),
            "button":        tx_button,
            "channel":       channel,
            "flags":         f"{flags:04b}",
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
        })


__all__ = ["ThermoProTX7B"]
