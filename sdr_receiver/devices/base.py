"""Base decoder classes for all rtl_433-compatible protocols.

To add a new device:
1. Choose the base class matching the modulation type.
2. Set class attributes (name, timings, n_bits).
3. Override _parse(bits, freq_hz) or decode(pulses, freq_hz).
4. Register an instance in __init__.DEVICE_REGISTRY.

Modulation type mapping from rtl_433 source:
  OOK_PULSE_PWM              → OOKPWMDecoder
  OOK_PULSE_PPM              → OOKPPMDecoder
  OOK_PULSE_PCM              → OOKPCMDecoder
  OOK_PULSE_MANCHESTER_*     → ManchesterDecoder
  FSK_PULSE_PCM              → FSKPCMDecoder
  FSK_PULSE_MANCHESTER_*     → FSKManchesterDecoder
  (complex / multi-mode)     → RawDecoder
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..dsp import (
    Pulse,
    bits_to_int,
    checksum_sum,
    crc8,
    crc16,
    demodulate_fsk,
    pulses_to_bits_manchester,
    pulses_to_bits_pcm,
    pulses_to_bits_ppm,
    pulses_to_bits_pwm,
)
from ..packet import DecodedPacket

__all__ = [
    "OOKPWMDecoder",
    "OOKPPMDecoder",
    "OOKPCMDecoder",
    "ManchesterDecoder",
    "FSKPCMDecoder",
    "FSKManchesterDecoder",
    "RawDecoder",
]


# ---------------------------------------------------------------------------
# OOK  Pulse Width Modulation
# ---------------------------------------------------------------------------

class OOKPWMDecoder(ABC):
    """OOK_PULSE_PWM: short pulse = 0, long pulse = 1."""
    name:       str   = "Unknown"
    short_us:   float = 500.0
    long_us:    float = 1_000.0
    reset_us:   float = 8_000.0
    n_bits:     int   = 0
    tolerance:  float = 0.45
    max_offset: int   = 5

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        data = [p for p in pulses if 50 < p.pulse_us < self.reset_us]
        if len(data) < self.n_bits:
            return None
        for off in range(min(self.max_offset, len(data) - self.n_bits + 1)):
            bits = pulses_to_bits_pwm(
                data[off : off + self.n_bits], self.short_us, self.long_us, self.tolerance
            )
            if bits is None:
                continue
            result = self._parse(bits, freq_hz)
            if result is not None:
                return result
        return None

    @abstractmethod
    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None: ...


# ---------------------------------------------------------------------------
# OOK  Pulse Position Modulation
# ---------------------------------------------------------------------------

class OOKPPMDecoder(ABC):
    """OOK_PULSE_PPM: short gap = 0, long gap = 1."""
    name:       str   = "Unknown"
    short_us:   float = 500.0
    long_us:    float = 1_000.0
    reset_us:   float = 8_000.0
    n_bits:     int   = 0
    tolerance:  float = 0.45
    max_offset: int   = 5

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        data = [p for p in pulses if p.pulse_us < self.reset_us]
        if len(data) < self.n_bits:
            return None
        for off in range(min(self.max_offset, len(data) - self.n_bits + 1)):
            bits = pulses_to_bits_ppm(
                data[off : off + self.n_bits], self.short_us, self.long_us, self.tolerance
            )
            if bits is None:
                continue
            result = self._parse(bits, freq_hz)
            if result is not None:
                return result
        return None

    @abstractmethod
    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None: ...


# ---------------------------------------------------------------------------
# OOK  Pulse Code Modulation / NRZ
# ---------------------------------------------------------------------------

class OOKPCMDecoder(ABC):
    """OOK_PULSE_PCM: fixed-width chips; high=1, low=0."""
    name:       str   = "Unknown"
    chip_us:    float = 500.0
    reset_us:   float = 8_000.0
    n_bits:     int   = 0
    inverted:   bool  = False
    tolerance:  float = 0.4
    max_offset: int   = 5

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        bits = pulses_to_bits_pcm(pulses, self.chip_us, self.inverted, self.tolerance)
        if bits is None or len(bits) < self.n_bits:
            return None
        for off in range(min(self.max_offset, len(bits) - self.n_bits + 1)):
            result = self._parse(bits[off : off + self.n_bits], freq_hz)
            if result is not None:
                return result
        return None

    @abstractmethod
    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None: ...


# ---------------------------------------------------------------------------
# OOK  Manchester Encoding
# ---------------------------------------------------------------------------

class ManchesterDecoder(ABC):
    """OOK_PULSE_MANCHESTER_ZEROBIT / NRZS: pairs of chips encode each bit."""
    name:       str   = "Unknown"
    chip_us:    float = 500.0
    reset_us:   float = 8_000.0
    n_bits:     int   = 0
    inverted:   bool  = False   # True = IEEE 802.3; False = G.E. Thomas
    tolerance:  float = 0.45
    max_offset: int   = 5

    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        data = [p for p in pulses if p.pulse_us < self.reset_us]
        bits = pulses_to_bits_manchester(data, self.chip_us, self.inverted, self.tolerance)
        if bits is None or len(bits) < self.n_bits:
            return None
        for off in range(min(self.max_offset, len(bits) - self.n_bits + 1)):
            result = self._parse(bits[off : off + self.n_bits], freq_hz)
            if result is not None:
                return result
        return None

    @abstractmethod
    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None: ...


# ---------------------------------------------------------------------------
# FSK  Pulse Code Modulation
# ---------------------------------------------------------------------------

class FSKPCMDecoder(ABC):
    """FSK_PULSE_PCM: CPFSK demodulation, then fixed-width bit decoding."""
    name:        str   = "Unknown"
    freq_hz:     float = 433.92e6
    bit_rate:    float = 10_000.0
    n_bits:      int   = 0
    sample_rate: int   = 250_000
    max_offset:  int   = 5

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        import numpy as np
        from ..dsp import demodulate_fsk
        bits_arr = demodulate_fsk(samples, sample_rate, self.bit_rate)
        bits = [int(b) for b in bits_arr]
        if len(bits) < self.n_bits:
            return None
        for off in range(min(self.max_offset, len(bits) - self.n_bits + 1)):
            result = self._parse(bits[off : off + self.n_bits], self.freq_hz)
            if result is not None:
                return result
        return None

    # For registry compatibility  OOK pipeline passes pulses, not samples.
    # FSK devices are handled separately by the UATReceiver / future FSK path.
    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None:
        return None

    @abstractmethod
    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None: ...


# ---------------------------------------------------------------------------
# FSK  Manchester Encoding
# ---------------------------------------------------------------------------

class FSKManchesterDecoder(FSKPCMDecoder):
    """FSK_PULSE_MANCHESTER_ZEROBIT: CPFSK + Manchester bit layer."""
    inverted: bool = False

    def decode_fsk(self, samples, sample_rate: int) -> DecodedPacket | None:
        from ..dsp import demodulate_fsk
        raw = demodulate_fsk(samples, sample_rate, self.bit_rate)
        us_per_chip = 1e6 / self.bit_rate
        bits = pulses_to_bits_manchester(
            _fsk_bits_to_pulses(raw, self.bit_rate), us_per_chip, self.inverted
        )
        if bits is None or len(bits) < self.n_bits:
            return None
        for off in range(len(bits) - self.n_bits + 1):
            result = self._parse(bits[off : off + self.n_bits], self.freq_hz)
            if result is not None:
                return result
        return None


def _fsk_bits_to_pulses(bits, bit_rate: float) -> list[Pulse]:
    """Convert an FSK bit array to a pulse list for Manchester decoding."""
    us_per_bit = 1e6 / bit_rate
    pulses: list[Pulse] = []
    i = 0
    while i < len(bits):
        level = bits[i]
        j = i + 1
        while j < len(bits) and bits[j] == level:
            j += 1
        count = j - i
        gap_count = 0
        if j < len(bits):
            k = j + 1
            while k < len(bits) and bits[k] != level:
                k += 1
            gap_count = k - j
        if level == 1:
            pulses.append(Pulse(
                pulse_us=count * us_per_bit,
                gap_us=gap_count * us_per_bit,
            ))
        i = j
    return pulses


# ---------------------------------------------------------------------------
# Escape hatch for complex / multi-mode protocols
# ---------------------------------------------------------------------------

class RawDecoder(ABC):
    """For protocols that don't fit OOK_PWM / OOK_PPM cleanly."""
    name: str = "Unknown"

    @abstractmethod
    def decode(self, pulses: list[Pulse], freq_hz: float) -> DecodedPacket | None: ...
