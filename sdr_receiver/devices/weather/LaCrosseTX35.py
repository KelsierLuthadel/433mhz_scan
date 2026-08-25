"""LaCrosse TX29IT / TX35DTHIT temperature (+ humidity) (FSK PCM, ~105 µs chips)."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import FSKPCMDecoder
from ...dsp import crc8
from ._helpers import _find_preamble, _extract_bytes
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class LaCrosseTX35(FSKPCMDecoder):
    """LaCrosse TX29IT / TX35DTHIT temperature (+ humidity) (FSK PCM, ~105 µs chips).

    Preamble: 0xa2 0xdd 0x49.  Payload: 5 bytes.
    CRC-8 poly 0x31 init 0x00 over first 4 bytes.
    Temperature: 10×nib1 + nib2 + 0.1×nib3 − 40 °C.
    """
    name     = "LaCrosse-TX35"
    bit_rate = 1e6 / 105.0   # ≈ 9524 bps
    n_bits   = 64

    _PREAMBLE = bytes([0xa2, 0xdd, 0x49])

    # Humidity values that indicate "no sensor"
    _NO_HUM = (0x6A, 0x00)

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        off = _find_preamble(bits, self._PREAMBLE)
        if off < 0 or off + 40 > len(bits):
            return None
        b = _extract_bytes(bits, off, 5)

        if crc8(b[:4], poly=0x31, init=0x00) != b[4]:
            return None

        sensor_id   = ((b[0] & 0x0F) << 2) | ((b[1] >> 6) & 0x03)
        new_battery = bool((b[1] >> 5) & 1)
        battery_ok  = not bool(b[3] >> 7)
        humidity    = b[3] & 0x7F
        temp_c      = (10 * (b[1] & 0x0F)
                       + ((b[2] >> 4) & 0x0F)
                       + 0.1 * (b[2] & 0x0F)
                       - 40.0)

        if not -40.0 <= temp_c <= 60.0:
            return None

        fields: dict = {
            "id": sensor_id, "battery_ok": battery_ok,
            "new_battery": new_battery, "temperature_C": round(temp_c, 1),
        }
        if humidity not in self._NO_HUM and 0 <= humidity <= 100:
            fields["humidity"] = humidity

        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["LaCrosseTX35"]
