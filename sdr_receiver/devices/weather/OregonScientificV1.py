"""OSv1 Temperature Sensor  custom OOK PWM with sync pulse."""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import RawDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class OregonScientificV1(RawDecoder):
    """OSv1 Temperature Sensor  custom OOK PWM with sync pulse.

    Modulation : OOK_PULSE_PWM (OSv1 variant)
    short_width: 1465 µs  (PWM threshold)
    sync_width : 5780 µs  (identifies start of frame)
    gap_limit  : 3500 µs
    reset_limit: 14000 µs

    Frame structure (32 bits = 8 nibbles):
      Nibble 0  : Sensor ID
      Nibble 1  : Channel (bits [3:2] + 1), unknown (bits [1:0])
      Nibble 2  : Temperature 0.1 °C digit (BCD)
      Nibble 3  : Temperature 1 °C digit   (BCD)
      Nibble 4  : Temperature 10 °C digit  (BCD, bit 3 = sign)
      Nibble 5  : Battery OK (bit 3), sign extension (bit 1)
      Nibble 6-7: Checksum (end-around carry of nibble sum, 8-bit)

    Pulse encoding:
      sync  pulse : pulse_us ≥ 4 500 µs  (nominal 5 780 µs)
      bit 0 pulse : pulse_us <  2 500 µs (nominal 1 748 µs)
      bit 1 pulse : pulse_us ≥  2 500 µs (nominal 3 216 µs)
    """

    name = "OSv1-Temperature"

    _SYNC_MIN_US  = 4_500   # lower bound for the sync pulse
    _BIT_THRESH_US = 2_500  # decision boundary: below → 0, above → 1
    _N_DATA_BITS  = 32

    def decode(self, pulses: "list[Pulse]", freq_hz: float) -> DecodedPacket | None:
        """Scan for the sync pulse then decode 32 PWM data bits."""
        if len(pulses) < self._N_DATA_BITS + 1:
            return None

        # Find sync pulse (significantly longer than data pulses)
        sync_idx = -1
        for i, p in enumerate(pulses):
            if p.pulse_us >= self._SYNC_MIN_US:
                sync_idx = i
                break

        if sync_idx < 0 or sync_idx + self._N_DATA_BITS >= len(pulses):
            return None

        # Decode 32 data bits following the sync: pulse_us determines bit value
        data_pulses = pulses[sync_idx + 1: sync_idx + 1 + self._N_DATA_BITS]
        if len(data_pulses) < self._N_DATA_BITS:
            return None

        bits = [1 if p.pulse_us >= self._BIT_THRESH_US else 0 for p in data_pulses]

        # Extract 8 nibbles
        nibs = [bits_to_int(bits[i: i + 4]) for i in range(0, 32, 4)]

        sensor_id = nibs[0]
        channel   = ((nibs[1] >> 2) & 0x03) + 1

        # BCD temperature digits; sign bit is nibble[4] bit 3
        if (nibs[2] & 0xF) > 9 or (nibs[3] & 0xF) > 9:
            return None
        temp_c = nibs[2] * 0.1 + nibs[3] + (nibs[4] & 0x07) * 10.0
        if nibs[4] & 0x08:
            temp_c = -temp_c
        if not -50.0 <= temp_c <= 70.0:
            return None

        battery_ok = bool(nibs[5] & 0x08)

        # End-around-carry checksum: sum nibbles 0-5, fold the carry into the sum
        nib_sum = sum(nibs[:6])
        chk_stored = nibs[6] | (nibs[7] << 4)
        # Two accepted fold methods (sensor firmware variants)
        chk_a = ((nib_sum & 0xFF) + (nib_sum >> 8)) & 0xFF
        chk_b = ((nib_sum + 1) if nib_sum > 0x180 else nib_sum) & 0xFF
        if chk_stored == 0 or chk_stored not in (chk_a, chk_b):
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            sensor_id,
            "channel":       channel,
            "battery_ok":    battery_ok,
            "temperature_C": round(temp_c, 1),
            "mic":           "CHECKSUM",
        })


__all__ = ["OregonScientificV1"]
