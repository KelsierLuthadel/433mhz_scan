"""SCM+ (SCMplus) electricity/gas/water meter message  ported from rtl_433 C source.

Note: scm_plus.c was not found in the rtl_433 repository at the expected path.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import ManchesterDecoder
from ...dsp import bits_to_int, crc16
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class ScmPlus(ManchesterDecoder):
    """ERT SCM+ (SCMplus) electricity/gas/water meter message.

    OOK_PULSE_MANCHESTER_ZEROBIT, chip=30 us, reset=64 us.
    Sync: 0x16 0xA3 0x1E (24 bits).
    Payload: 16 bytes (128 bits) after sync.
    CRC-16/CCITT poly=0x1021 init=0x0971 non-reflecting over payload bytes[2:14];
    stored in bytes[14:16].
    Payload fields:
      byte[2]     – protocol ID
      byte[3]     – endpoint type (low nibble: meter category)
      bytes[4:8]  – endpoint ID (32-bit BE)
      bytes[8:12] – consumption data (32-bit BE)
      bytes[12:14]– tamper flags (16-bit BE)
      bytes[14:16]– CRC-16
    Meter type from endpoint_type & 0x0F:
      Electric: 4,5,7,8 | Gas: 0,1,2,9,12 | Water: 3,11,13
    """
    name = "SCMplus"
    chip_us = 30.0
    reset_us = 64.0
    n_bits = 152  # 24 sync + 128 payload

    _SYNC = bytes((0x16, 0xA3, 0x1E))
    _METER_TYPES: dict[int, str] = {
        4: "Electric", 5: "Electric", 7: "Electric", 8: "Electric",
        0: "Gas",      1: "Gas",      2: "Gas",      9: "Gas",      12: "Gas",
        3: "Water",   11: "Water",   13: "Water",
    }

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 152:
            return None

        # Search for 24-bit sync pattern 0x16 0xA3 0x1E within received bits.
        search_end = max(1, len(bits) - 152 + 1)
        payload_start = -1
        for off in range(0, search_end, 8):
            if off + 24 > len(bits):
                break
            b0 = bits_to_int(bits[off:      off + 8])
            b1 = bits_to_int(bits[off + 8:  off + 16])
            b2 = bits_to_int(bits[off + 16: off + 24])
            if bytes((b0, b1, b2)) == self._SYNC:
                payload_start = off + 24
                break

        if payload_start < 0 or len(bits) < payload_start + 128:
            return None

        # Extract 16-byte payload.
        payload = bytes(
            bits_to_int(bits[payload_start + i * 8: payload_start + i * 8 + 8])
            for i in range(16)
        )

        # CRC-16/CCITT over payload bytes[2:14]; compare against bytes[14:16].
        crc_calc = crc16(payload[2:14], poly=0x1021, init=0x0971,
                         ref_in=False, ref_out=False)
        crc_recv = (payload[14] << 8) | payload[15]
        if crc_calc != crc_recv:
            return None

        protocol_id  = payload[2]
        endpoint_type = payload[3]
        endpoint_id  = (payload[4] << 24) | (payload[5] << 16) | (payload[6] << 8) | payload[7]
        consumption  = (payload[8] << 24) | (payload[9] << 16) | (payload[10] << 8) | payload[11]
        tamper       = (payload[12] << 8) | payload[13]
        meter_type   = self._METER_TYPES.get(endpoint_type & 0x0F, "Unknown")

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           endpoint_id,
            "ProtocolID":   protocol_id,
            "EndpointType": endpoint_type,
            "Consumption":  consumption,
            "Tamper":       tamper,
            "MeterType":    meter_type,
            "PacketCRC":    crc_recv,
            "mic":          "CRC",
        })


__all__ = ["ScmPlus"]
