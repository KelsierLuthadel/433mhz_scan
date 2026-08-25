"""Oregon Scientific SL109H Remote Thermal Hygro Sensor."""
from __future__ import annotations
from ..base import OOKPPMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket


class OregonScientificSL109H(OOKPPMDecoder):
    """Oregon Scientific SL109H Remote Thermal Hygro Sensor.

    Modulation : OOK_PULSE_PPM
    short_width: 2000 µs  (short gap = bit 0)
    long_width : 4000 µs  (long  gap = bit 1)
    gap_limit  : 5000 µs
    reset_limit: 10000 µs

    38-bit frame layout (MSB-first):
      [AAAA] [CC] [HHHH HHHH] [TTTT TTTT TTTT] [SSSS] [IIII IIII]
       csum   ch   humidity      temperature       stat   device-id

      A (4 bits) : additive checksum (low nibble of nibble sum)
      C (2 bits) : channel code (1→ch1, 2→ch2, 0→ch3; 3=invalid)
      H (8 bits) : BCD humidity (tens×10 + units)
      T (12 bits): signed temperature × 10 (°C)
      S (4 bits) : status flags
      I (8 bits) : random sensor identifier
    """

    name     = "Oregon-Scientific-SL109H"
    short_us = 2000.0
    long_us  = 4000.0
    reset_us = 10000.0
    n_bits   = 38

    # Channel code → logical channel number  (code 3 is invalid)
    _CH_MAP = {0: 3, 1: 1, 2: 2}

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 38:
            return None

        # Reject all-zero frames (radio noise / squelch artifact)
        if not any(bits[:38]):
            return None

        checksum  = bits_to_int(bits[0:4])
        ch_code   = bits_to_int(bits[4:6])
        hum_raw   = bits_to_int(bits[6:14])    # BCD byte
        temp_raw  = bits_to_int(bits[14:26])   # 12-bit signed
        status    = bits_to_int(bits[26:30])
        device_id = bits_to_int(bits[30:38])

        # Channel validation
        if ch_code not in self._CH_MAP:
            return None
        channel = self._CH_MAP[ch_code]

        # BCD humidity (packed as [tens nibble][units nibble])
        hum_tens  = (hum_raw >> 4) & 0xF
        hum_units =  hum_raw & 0xF
        if hum_tens > 9 or hum_units > 9:
            return None
        humidity = hum_tens * 10 + hum_units

        # 12-bit signed temperature, scaled × 10
        if temp_raw >= 2048:
            temp_raw -= 4096
        temp_c = temp_raw / 10.0
        if not -20.0 <= temp_c <= 60.0:
            return None

        # Nibble checksum: sum of 8 nibbles spanning bits[6:38] (32 bits),
        # lower nibble of the sum must equal the 4-bit checksum field.
        # Bits 4-5 (channel code) are sub-nibble and merged into the first
        # counted nibble as bits[4:8].
        nibble_sum = sum(bits_to_int(bits[4 + i * 4: 8 + i * 4]) for i in range(8)) & 0xF
        if nibble_sum != checksum:
            return None

        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":            device_id,
            "channel":       channel,
            "temperature_C": round(temp_c, 1),
            "humidity":      humidity,
            "status":        status,
            "mic":           "CHECKSUM",
        })


__all__ = ["OregonScientificSL109H"]
