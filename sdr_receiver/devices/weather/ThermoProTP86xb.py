"""ThermoPro TempSpike XR TP862b / TP863b Dual-Probe Meat Thermometer (FSK PCM 104 µs)."""
from __future__ import annotations
from ..base import RawDecoder
from ...dsp import crc8
from ._helpers import _fsk_pcm_to_bits, _find_preamble, _extract_bytes
from ...packet import DecodedPacket


class ThermoProTP86xb(RawDecoder):
    """ThermoPro TempSpike XR TP862b / TP863b Dual-Probe Meat Thermometer
    (FSK PCM 104 µs).

    Preamble: 0xD2 0x55 0x2D 0xD4 (32 bits).
    Payload: 9 bytes (72 bits)  id[8] | flags[8] | internal[12] |
             ambient[12] | device-type+battery[16] | CRC-A[8] | CRC-B[8].
    Integrity: CRC-8 (poly=0x07, init=0x00, XOR=0xDB) over bytes 0–6 → byte 7.
               byte7 & byte8 must be disjoint (probe vs booster distinguish).
    temp_C = (raw - 500) * 0.1
    """

    _CHIP_US  = 104.0
    _PREAMBLE = bytes([0xD2, 0x55, 0x2D, 0xD4])

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:
        bits   = _fsk_pcm_to_bits(pulses, self._CHIP_US)
        offset = _find_preamble(bits, self._PREAMBLE)
        if offset < 0 or (len(bits) - offset) < 72:
            return None
        b = _extract_bytes(bits, offset, 9)
        # Bytes 7 and 8 must not share any 1-bits
        if b[7] & b[8]:
            return None
        # CRC-8, poly=0x07, init=0x00, final XOR=0xDB, over bytes 0–6
        if (crc8(b[:7], 0x07, 0x00) ^ 0xDB) != b[7]:
            return None

        id_          = b[0]
        is_white     = bool((b[1] & 0x10) >> 4)
        is_docked    = bool((b[1] & 0x40) >> 6)
        internal_raw = (b[2] << 4) | (b[3] >> 4)
        ambient_raw  = ((b[3] & 0x0F) << 8) | b[4]
        is_probe     = (b[6] & 0x0C) == 0x0C
        is_booster   = (b[5] & 0xC0) == 0xC0
        probe_bat    = (b[6] & 0x30) >> 4
        booster_bat  = b[6] & 0x03

        fields: dict = {
            "id":                 f"{id_:02x}",
            "color":              "white" if is_white else "black",
            "temperature_int_C":  round((internal_raw - 500) * 0.1, 1),
            "temperature_amb_C":  round((ambient_raw  - 500) * 0.1, 1),
        }
        if is_docked:
            fields["is_docked"] = 1
        if is_probe:
            fields["is_probe"]       = 1
            fields["probe_battery"]  = probe_bat
        if is_booster:
            fields["is_booster"]      = 1
            fields["booster_battery"] = booster_bat
        return DecodedPacket.from_fields("ThermoPro-TempSpikeXR", freq_hz, fields)


__all__ = ["ThermoProTP86xb"]
