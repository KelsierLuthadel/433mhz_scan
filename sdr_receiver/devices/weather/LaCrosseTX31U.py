"""LaCrosse TX31U-IT / Weather Channel WS-1910TWC-IT (FSK PCM, ~116 µs chips)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseTX31U(FSKPCMDecoder):
    """LaCrosse TX31U-IT / Weather Channel WS-1910TWC-IT (FSK PCM, ~116 µs chips).

    Preamble: 0xaa 0xaa 0x2d 0xd4.
    Header: 2 bytes → sensor_id(6b), battery(1b), n_meas(3b).
    Measurements: n_meas × 2 bytes (type:4b + 3 value nibbles).
    CRC-8 poly 0x31 init 0x00 over 2 + n_meas*2 bytes.
    Sensor types: 0=temp, 1=hum, 2=rain, 3=wind_avg+dir, 4=wind_gust.
    """
    name     = "LaCrosse-TX31U"
    bit_rate = 1e6 / 116.0
    n_bits   = 96

    _PREAMBLE = bytes([0xaa, 0xaa, 0x2d, 0xd4])

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        off = _find_preamble(bits, self._PREAMBLE)
        if off < 0:
            return None
        avail = (len(bits) - off) // 8
        if avail < 4:
            return None
        hdr = _extract_bytes(bits, off, min(avail, 16))

        sensor_id  = ((hdr[0] & 0x0F) << 2) | ((hdr[1] >> 6) & 0x03)
        battery_ok = not bool(hdr[1] & 0x08)
        n_meas     = hdr[1] & 0x07
        expected   = 2 + n_meas * 2 + 1

        if len(hdr) < expected:
            return None

        crc_data = hdr[:2 + n_meas * 2]
        crc_recv = hdr[2 + n_meas * 2]
        if crc8(bytes(crc_data), poly=0x31, init=0x00) != crc_recv:
            return None

        fields: dict = {"id": sensor_id, "battery_ok": battery_ok}

        for i in range(n_meas):
            idx    = 2 + i * 2
            q_type = (hdr[idx] >> 4) & 0xF
            nib1   =  hdr[idx] & 0xF
            nib2   = (hdr[idx + 1] >> 4) & 0xF
            nib3   =  hdr[idx + 1] & 0xF

            if q_type == 0:
                fields["temperature_C"] = round(10 * nib1 + nib2 + 0.1 * nib3 - 40.0, 1)
            elif q_type == 1:
                fields["humidity"] = 100 * nib1 + 10 * nib2 + nib3
            elif q_type == 2:
                fields["rain_raw"] = (nib1 << 8) | (nib2 << 4) | nib3
            elif q_type == 3:
                fields["wind_dir_deg"]  = nib1 * 22.5
                fields["wind_avg_km_h"] = round(((nib2 << 4) | nib3) * 0.1 * 3.6, 1)
            elif q_type == 4:
                fields["wind_max_km_h"] = round(((nib2 << 4) | nib3) * 0.1 * 3.6, 1)

        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["LaCrosseTX31U"]
