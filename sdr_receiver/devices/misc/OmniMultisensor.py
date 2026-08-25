"""Omni Multisensor (OOK_PULSE_PWM, 80 bits)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int, crc8
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class OmniMultisensor(OOKPWMDecoder):
    """Omni Multisensor."""
    name     = "Omni-Multisensor"
    short_us = 200.0
    long_us  = 400.0
    reset_us = 1250.0
    n_bits   = 80

    def _parse(self, bits, freq_hz):
        if len(bits) < 80:
            return None
        b = bytearray(bits_to_int(bits[i:i + 8]) for i in range(0, 80, 8))
        # CRC-8, poly=0x97, init=0xaa over first 9 bytes
        if crc8(bytes(b[:9]), poly=0x97, init=0xaa) != b[9]:
            return None
        fmt    = (b[0] >> 4) & 0xF
        dev_id = b[0] & 0xF
        # payload bits are bits[8..] mapping to bytes b[1..8]
        payload_bits = bits[8:72]
        fields: dict = {"format": fmt, "id": dev_id}
        if fmt == 0:
            raw_t = bits_to_int(payload_bits[0:12])
            if raw_t >= 2048:
                raw_t -= 4096
            fields["core_temperature_C"] = round(raw_t / 10.0, 1)
            fields["voltage_V"]          = round(3.00 + b[4] / 100.0, 2)
        elif fmt == 1:
            raw_ti = bits_to_int(payload_bits[0:12])
            raw_to = bits_to_int(payload_bits[12:24])
            if raw_ti >= 2048: raw_ti -= 4096
            if raw_to >= 2048: raw_to -= 4096
            fields["temperature_in_C"]  = round(raw_ti / 10.0, 1)
            fields["temperature_out_C"] = round(raw_to / 10.0, 1)
            fields["humidity_in"]       = b[5]
            fields["humidity_out"]      = b[6]
            raw_p = (b[7] << 8) | b[8]
            fields["pressure_hPa"]      = round(raw_p / 10.0, 1)
        else:
            fields["data"] = bytes(b[1:9]).hex()
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["OmniMultisensor"]
