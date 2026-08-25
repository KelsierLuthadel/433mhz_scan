"""Oregon Scientific WMR500 Weather Station  FSK PCM decoder stub."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import crc16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class OregonScientificWMR500(RawDecoder):
    """Oregon Scientific WMR500 Weather Station  FSK PCM decoder stub.

    Modulation : FSK_PULSE_PCM (~26 µs chip width, inverted levels)
    short_width: 26 µs
    long_width : 26 µs
    reset_limit: 312 µs

    FSK devices are demodulated by the SDR front-end before they reach the
    pulse-level decoder pipeline; the standard OOK pulse list provided to
    ``decode()`` does not carry FSK content.  This class therefore returns
    ``None`` from ``decode()`` and is a placeholder for future FSK pipeline
    integration.

    Frame structure (long message, LEN=25, 28 bytes):
      Byte  0    : Length (14 = short header, 25 = weather data)
      Byte  1    : 0xFE (fixed)
      Bytes 8-9  : Device ID (big-endian)
      Byte  14   : Temperature raw  → (raw − 169) × 0.7 °C
      Byte  16   : Humidity raw     → 208 − raw
      Bytes 26-27: CRC-16 (poly 0x8005, init 0x1A4C) over bytes 0-25

    Preamble (inverted domain): 0x55 0x2C 0x6E 0x2C 0x6E (40 bits)
    """

    name = "Oregon-Scientific-WMR500"

    # CRC-16 parameters used by WMR500
    _CRC_POLY = 0x8005
    _CRC_INIT = 0x1A4C

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        # FSK signals cannot be decoded from an OOK pulse list.
        # WMR500 decoding requires the FSK sample-level pipeline.
        return None

    def decode_bytes(self, data: bytes, freq_hz: float) -> DecodedPacket | None:
        """Decode a pre-demodulated WMR500 byte frame (for FSK pipeline use).

        *data* must begin at the first byte after the 5-byte preamble and
        contain at least 28 bytes for a long (weather) message.
        """
        if len(data) < 2:
            return None

        msg_len = data[0]
        if data[1] != 0xFE:
            return None

        if msg_len == 14:
            # Short header message: device ID only
            if len(data) < 10:
                return None
            device_id = (data[8] << 8) | data[9]
            return DecodedPacket.from_fields(self.name, freq_hz, {
                "id": f"{device_id:04X}",
            })

        if msg_len != 25 or len(data) < 28:
            return None

        # CRC-16 over bytes 0-25
        crc_calc = crc16(data[:26], poly=self._CRC_POLY, init=self._CRC_INIT,
                         ref_in=False, ref_out=False)
        crc_recv = (data[26] << 8) | data[27]
        if crc_calc != crc_recv:
            return None

        device_id = (data[8] << 8) | data[9]
        temp_c    = (data[14] - 169) * 0.7
        humidity  = 208 - data[16]

        if not -40.0 <= temp_c <= 60.0:
            return None
        if not 0 <= humidity <= 100:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            f"{device_id:04X}",
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
            "mic":           "CRC",
        })


__all__ = ["OregonScientificWMR500"]
