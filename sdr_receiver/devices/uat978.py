"""UAT 978 MHz ADS-B decoder.

Modulation : CPFSK, ±312.5 kHz deviation
Bit rate   : 1 041 667 bps
Sync words : 0xEACDDA4E  (uplink / air-to-ground)
             0x153225B1  (downlink / ground-to-air)

Basic UAT frame (after sync): 144 data bits + 96 FEC bits.
This decoder extracts ICAO address, lat/lon and altitude from the data
payload without a full Reed-Solomon pass  packets with bit errors may
produce garbled fields; they are rejected via range checks.
"""

from __future__ import annotations

import numpy as np

from ..packet import DecodedPacket

UAT_BIT_RATE   = 1_041_667.0
SYNC_UPLINK    = 0xEACDDA4E
SYNC_DOWNLINK  = 0x153225B1
BASIC_DATA_BITS = 144


def _find_sync(bits: np.ndarray, sync_word: int, tolerance: int = 2) -> list[int]:
    pattern = np.array([(sync_word >> (31 - i)) & 1 for i in range(32)], dtype=np.uint8)
    positions = []
    for i in range(len(bits) - 32):
        if int(np.sum(bits[i : i + 32] != pattern)) <= tolerance:
            positions.append(i)
    return positions


def _bits_to_int(bits: np.ndarray) -> int:
    result = 0
    for b in bits:
        result = (result << 1) | int(b)
    return result


class UATDecoder:
    name = "UAT-978"

    def decode_chunk(
        self, samples: np.ndarray, sample_rate: int
    ) -> list[DecodedPacket]:
        from ..dsp import demodulate_fsk

        bits = demodulate_fsk(samples, sample_rate, UAT_BIT_RATE)
        packets: list[DecodedPacket] = []

        for sync_word, direction in (
            (SYNC_UPLINK,   "uplink"),
            (SYNC_DOWNLINK, "downlink"),
        ):
            for pos in _find_sync(bits, sync_word, tolerance=2):
                payload_start = pos + 32
                if payload_start + BASIC_DATA_BITS > len(bits):
                    continue
                payload = bits[payload_start : payload_start + BASIC_DATA_BITS]
                pkt = self._decode_payload(payload, direction)
                if pkt is not None:
                    packets.append(pkt)

        return packets

    def _decode_payload(
        self, payload: np.ndarray, direction: str
    ) -> DecodedPacket | None:
        if len(payload) < 53:
            return None

        # Message type (bits 0-4)
        msg_type = _bits_to_int(payload[0:5])

        # ICAO / self-assigned address (bits 5-28)
        icao = _bits_to_int(payload[5:29])

        # Altitude (bits 29-40, 12 bits)  raw * 25 − 1000 ft
        alt_raw = _bits_to_int(payload[29:41])
        altitude_ft = alt_raw * 25 - 1_000

        # Latitude (bits 41-57, 17 bits, signed)
        lat_raw = _bits_to_int(payload[41:58])
        if lat_raw >= 2**16:
            lat_raw -= 2**17
        lat = round(lat_raw * 360.0 / 2**17, 6)

        # Longitude (bits 58-74, 17 bits, signed)
        lon_raw = _bits_to_int(payload[58:75])
        if lon_raw >= 2**16:
            lon_raw -= 2**17
        lon = round(lon_raw * 360.0 / 2**17, 6)

        # Sanity
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return None

        fields: dict = {
            "direction":   direction,
            "msg_type":    msg_type,
            "icao":        f"{icao:06X}",
            "altitude_ft": altitude_ft,
            "latitude":    lat,
            "longitude":   lon,
        }

        return DecodedPacket.from_fields(
            model=self.name,
            freq_hz=978e6,
            fields=fields,
        )
