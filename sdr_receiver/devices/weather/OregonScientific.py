"""Oregon Scientific v2.1 multi-sensor weather station decoder."""
from __future__ import annotations
from ..base import ManchesterDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


# ---------------------------------------------------------------------------
# Helpers shared by the Oregon Scientific v2.1 protocol
# ---------------------------------------------------------------------------

def _reflect_nibble(n: int) -> int:
    """Bit-reverse a 4-bit nibble (transmit bit order → logical bit order)."""
    return ((n & 0x1) << 3) | ((n & 0x2) << 1) | ((n & 0x4) >> 1) | ((n & 0x8) >> 3)


def _os_nibbles(bits: list[int], start: int, count: int) -> list[int]:
    """Extract *count* nibbles from *bits* starting at bit index *start*.

    Each nibble's bits arrive LSB-first (Oregon Scientific convention), so we
    bit-reverse within each group of four.
    """
    nibs: list[int] = []
    for i in range(count):
        base = start + i * 4
        raw = bits_to_int(bits[base: base + 4])
        nibs.append(_reflect_nibble(raw))
    return nibs


def _os_v2_checksum_ok(nibs: list[int], n_data: int) -> bool:
    """Validate the Oregon Scientific v2.1 nibble checksum.

    The 1-byte checksum is the sum (mod 256) of the first *n_data* nibbles.
    It is stored as two nibbles (low then high) immediately after the data.
    """
    if len(nibs) < n_data + 2:
        return False
    total = sum(nibs[:n_data]) & 0xFF
    stored = nibs[n_data] | (nibs[n_data + 1] << 4)
    return total == stored


# Map from 16-bit Oregon Scientific v2 sensor ID → (model name, sensor class)
# IDs are the nibble-reflected 4-nibble value formed from the first 2 bytes.
_OS_SENSORS: dict[int, tuple[str, str]] = {
    0x1d20: ("THGR122N",  "thgr"),
    0x1d30: ("THGR968",   "thgr"),
    0xf824: ("THGR810",   "thgr"),
    0xca48: ("THGR810",   "thgr"),
    0xec40: ("THN122N",   "thn"),
    0xc844: ("THGR800",   "thgr"),
    0x5d60: ("THGR238",   "thgr"),
    0x0900: ("PCR800",    "pcr"),
    0x2914: ("PCR800",    "pcr"),
    0x1984: ("WGR800",    "wgr"),
    0x3d00: ("WGR918",    "wgr"),
    0x6975: ("UVN800",    "uvn"),
    0x8f04: ("THN800",    "thn"),
}


class OregonScientific(ManchesterDecoder):
    """Oregon Scientific v2.1 multi-sensor weather station decoder.

    Modulation : OOK_PULSE_MANCHESTER_ZEROBIT
    short_width: 440 µs  (nominal Manchester chip = 488 µs)
    reset_limit: 2400 µs

    After Manchester decoding the bit stream contains:
      • Preamble  – repeated alternating chips (~18+ bits)
      • Sync nibble 0xA (raw = 1,0,1,0 before reflection)
      • Sensor ID  – 4 nibbles (each bit-reversed = LSB-first)
      • Channel / device-ID / battery nibbles
      • Sensor-type-specific payload nibbles
      • 2-nibble checksum (low byte then high byte of nibble sum)

    Sensor types implemented: THGR* temperature+humidity, THN* temperature-only,
    WGR* wind, PCR* precipitation, UVN* UV index.  Unknown sensor IDs return
    raw nibbles as a hex string so the frame is not silently dropped.
    """

    name     = "Oregon-Scientific"
    chip_us  = 440.0
    reset_us = 2400.0
    n_bits   = 200     # generous window; sync is located inside _parse
    inverted = False
    tolerance = 0.45

    # The sync nibble value in the raw (pre-reflection) bit stream
    _SYNC_RAW = 0xA   # binary 1010  marks end of preamble

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        # ------------------------------------------------------------------
        # Locate the sync nibble (0xA = 1,0,1,0 in raw stream order).
        # The preamble may contain the same pattern, so require that enough
        # bits remain after the candidate sync position.
        # ------------------------------------------------------------------
        sync_pos = -1
        for i in range(0, len(bits) - 4):
            if bits_to_int(bits[i: i + 4]) == self._SYNC_RAW:
                # Need at least 16 nibbles (64 bits) of payload after sync
                if i + 4 + 64 <= len(bits):
                    sync_pos = i + 4
                    break

        if sync_pos < 0:
            return None

        max_nibs = (len(bits) - sync_pos) // 4
        if max_nibs < 12:
            return None

        nibs = _os_nibbles(bits, sync_pos, max_nibs)

        # First two bytes (4 nibbles) carry the sensor ID.
        # Oregon Scientific packs them as: nibble[1]<<12 | nibble[0]<<8 |
        #                                  nibble[3]<<4  | nibble[2]
        sensor_id = (nibs[1] << 12) | (nibs[0] << 8) | (nibs[3] << 4) | nibs[2]

        model_name, sensor_cls = _OS_SENSORS.get(sensor_id, (f"OS-{sensor_id:04X}", "unknown"))

        # Nibble 4: low 2 bits = channel (1-based), bit 2 = battery-ok flag
        channel    = (nibs[4] & 0x03) + 1
        battery_ok = bool((nibs[4] >> 2) & 0x01)
        # Nibble 5: rolling device ID (byte 3 lower nibble)
        device_id  = nibs[5]

        fields: dict = {
            "id":         device_id,
            "channel":    channel,
            "battery_ok": battery_ok,
        }

        if sensor_cls in ("thgr",):
            # Temperature: BCD, nibbles 6-8 = 0.1 °C, 1 °C, 10 °C + sign(bit3)
            if max_nibs < 16 or any(nibs[j] & 0x0F > 9 for j in (6, 7)):
                return None
            temp_c = nibs[6] * 0.1 + nibs[7] + (nibs[8] & 0x07) * 10.0
            if nibs[8] & 0x08:
                temp_c = -temp_c
            if not -50.0 <= temp_c <= 70.0:
                return None
            # Humidity: nibbles 9 (units) and 10 (tens)
            humidity = nibs[9] + nibs[10] * 10
            if not 0 <= humidity <= 100:
                return None
            if not _os_v2_checksum_ok(nibs, 12):
                return None
            fields.update({
                "temperature_C": round(temp_c, 1),
                "humidity":      humidity,
                "mic":           "CHECKSUM",
            })

        elif sensor_cls == "thn":
            # Temperature only (no humidity nibbles)
            if max_nibs < 14 or any(nibs[j] & 0x0F > 9 for j in (6, 7)):
                return None
            temp_c = nibs[6] * 0.1 + nibs[7] + (nibs[8] & 0x07) * 10.0
            if nibs[8] & 0x08:
                temp_c = -temp_c
            if not -50.0 <= temp_c <= 70.0:
                return None
            if not _os_v2_checksum_ok(nibs, 10):
                return None
            fields.update({
                "temperature_C": round(temp_c, 1),
                "mic":           "CHECKSUM",
            })

        elif sensor_cls == "wgr":
            # Wind: gust (nibs 6-8), average (nibs 9-11), direction (nibs 12-13)
            if max_nibs < 18:
                return None
            wind_gust = (nibs[6] + nibs[7] * 10 + nibs[8] * 100) * 0.1
            wind_avg  = (nibs[9] + nibs[10] * 10 + nibs[11] * 100) * 0.1
            wind_dir  = (nibs[12] + nibs[13] * 10) * 22.5
            if wind_gust > 56.0 or wind_avg > 56.0:
                return None
            if not _os_v2_checksum_ok(nibs, 14):
                return None
            fields.update({
                "wind_max_m_s": round(wind_gust, 1),
                "wind_avg_m_s": round(wind_avg, 1),
                "wind_dir_deg": round(wind_dir, 1),
                "mic":          "CHECKSUM",
            })

        elif sensor_cls == "pcr":
            # Rain rate (nibs 6-9) and total rain (nibs 10-15)
            if max_nibs < 20:
                return None
            rain_rate = (
                nibs[6] + nibs[7] * 10 + nibs[8] * 100 + nibs[9] * 1000
            ) * 0.01
            rain_total = (
                nibs[10] + nibs[11] * 10 + nibs[12] * 100
                + nibs[13] * 1000 + nibs[14] * 10_000 + nibs[15] * 100_000
            ) * 0.001
            if not _os_v2_checksum_ok(nibs, 16):
                return None
            fields.update({
                "rain_rate_mm_h": round(rain_rate, 2),
                "rain_total_mm":  round(rain_total, 3),
                "mic":            "CHECKSUM",
            })

        elif sensor_cls == "uvn":
            # UV index: nibs 6-7 (BCD)
            if max_nibs < 12:
                return None
            uv_index = nibs[6] + nibs[7] * 10
            if not _os_v2_checksum_ok(nibs, 8):
                return None
            fields.update({
                "uvi": uv_index,
                "mic": "CHECKSUM",
            })

        else:
            # Unknown sensor  pass raw nibbles as hex for diagnostics
            fields["raw_nibs"] = "".join(f"{n:x}" for n in nibs[:max_nibs])

        return DecodedPacket.from_fields(model_name, freq_hz, fields)


__all__ = ["OregonScientific"]
