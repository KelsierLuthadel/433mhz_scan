"""Signal processing: I/Q samples → OOK pulses / FSK bits / bit decoding."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# A gap longer than this (µs) separates distinct OOK packets.
RESET_GAP_US = 8_000.0


@dataclass
class Pulse:
    """One OOK symbol: a HIGH period followed by a LOW period."""
    pulse_us: float
    gap_us: float


# ---------------------------------------------------------------------------
# OOK demodulation
# ---------------------------------------------------------------------------

def demodulate_ook(
    samples: np.ndarray,
    sample_rate: int,
    threshold: float = 0.5,
    hysteresis: float = 0.15,
    smooth_us: float = 50.0,
) -> list[Pulse]:
    """Convert complex I/Q samples to a list of OOK pulses.

    Returns an empty list when the chunk is silent or too short.
    """
    mag = np.abs(samples).astype(np.float32)

    window = max(1, int(sample_rate * smooth_us * 1e-6))
    if window > 1:
        mag = np.convolve(mag, np.ones(window) / window, mode="same")

    peak = float(mag.max())
    if peak < 1e-6:
        return []
    mag /= peak

    hi = threshold
    lo = threshold - hysteresis
    us_per_sample = 1e6 / sample_rate

    state = bool(mag[0] > hi)
    transitions: list[tuple[int, bool]] = []
    for i in range(1, len(mag)):
        if not state and mag[i] > hi:
            state = True
            transitions.append((i, True))
        elif state and mag[i] < lo:
            state = False
            transitions.append((i, False))

    pulses: list[Pulse] = []
    i = 0
    while i < len(transitions) and not transitions[i][1]:
        i += 1

    while i + 1 < len(transitions):
        rise = transitions[i][0]
        fall = transitions[i + 1][0]
        next_rise = transitions[i + 2][0] if i + 2 < len(transitions) else fall + int(RESET_GAP_US * 2 / us_per_sample)

        pulse_us = (fall - rise) * us_per_sample
        gap_us = (next_rise - fall) * us_per_sample

        if pulse_us >= 100:
            pulses.append(Pulse(pulse_us=pulse_us, gap_us=gap_us))
        i += 2

    return pulses


def extract_packets(
    pulses: list[Pulse],
    reset_us: float = RESET_GAP_US,
    min_pulses: int = 8,
) -> list[list[Pulse]]:
    """Split a pulse stream into packet-sized groups at reset gaps."""
    packets: list[list[Pulse]] = []
    current: list[Pulse] = []
    for p in pulses:
        current.append(p)
        if p.gap_us >= reset_us:
            if len(current) >= min_pulses:
                packets.append(current)
            current = []
    if len(current) >= min_pulses:
        packets.append(current)
    return packets


# ---------------------------------------------------------------------------
# Bit encoding decoders
# ---------------------------------------------------------------------------

def pulses_to_bits_pwm(
    pulses: list[Pulse],
    short_us: float,
    long_us: float,
    tolerance: float = 0.45,
) -> list[int] | None:
    """PWM: short pulse → 0, long pulse → 1.  None if any pulse doesn't fit."""
    bits: list[int] = []
    for p in pulses:
        if short_us * (1 - tolerance) <= p.pulse_us <= short_us * (1 + tolerance):
            bits.append(0)
        elif long_us * (1 - tolerance) <= p.pulse_us <= long_us * (1 + tolerance):
            bits.append(1)
        else:
            return None
    return bits


def pulses_to_bits_ppm(
    pulses: list[Pulse],
    short_us: float,
    long_us: float,
    tolerance: float = 0.45,
) -> list[int] | None:
    """PPM: short gap → 0, long gap → 1.  None if any gap doesn't fit."""
    bits: list[int] = []
    for p in pulses:
        if short_us * (1 - tolerance) <= p.gap_us <= short_us * (1 + tolerance):
            bits.append(0)
        elif long_us * (1 - tolerance) <= p.gap_us <= long_us * (1 + tolerance):
            bits.append(1)
        else:
            return None
    return bits


# ---------------------------------------------------------------------------
# FSK demodulation
# ---------------------------------------------------------------------------

def demodulate_fsk(
    samples: np.ndarray,
    sample_rate: int,
    bit_rate: float,
) -> np.ndarray:
    """CPFSK demodulation: returns a uint8 bit array (0/1 per bit)."""
    phase_diff = np.angle(samples[1:] * np.conj(samples[:-1]))
    sps = sample_rate / bit_rate
    n_bits = int(len(phase_diff) / sps)
    bits = np.zeros(n_bits, dtype=np.uint8)
    for b in range(n_bits):
        s = int(b * sps)
        e = min(int((b + 1) * sps), len(phase_diff))
        bits[b] = 1 if float(np.mean(phase_diff[s:e])) > 0 else 0
    return bits


# ---------------------------------------------------------------------------
# Bit manipulation helpers
# ---------------------------------------------------------------------------

def pulses_to_bits_pcm(
    pulses: list[Pulse],
    chip_us: float,
    inverted: bool = False,
    tolerance: float = 0.4,
) -> list[int] | None:
    """OOK PCM/NRZ: count chips in each pulse and gap. High=1, Low=0."""
    bits: list[int] = []
    for p in pulses:
        n_high = round(p.pulse_us / chip_us)
        n_low  = round(p.gap_us  / chip_us)
        if n_high < 1 or abs(p.pulse_us - n_high * chip_us) > chip_us * tolerance:
            return None
        bits.extend([0 if inverted else 1] * n_high)
        if n_low > 0:
            bits.extend([1 if inverted else 0] * n_low)
    return bits or None


def pulses_to_bits_manchester(
    pulses: list[Pulse],
    chip_us: float,
    inverted: bool = False,
    tolerance: float = 0.45,
) -> list[int] | None:
    """Manchester encoding: expand pulses to chips then decode pairs.

    G.E. Thomas convention (default):  [1,0]=1  [0,1]=0
    IEEE 802.3 (inverted=True):        [1,0]=0  [0,1]=1
    """
    lo1 = chip_us * (1 - tolerance)
    hi1 = chip_us * (1 + tolerance)
    lo2 = chip_us * 2 * (1 - tolerance)
    hi2 = chip_us * 2 * (1 + tolerance)

    chips: list[int] = []
    for p in pulses:
        if lo1 <= p.pulse_us <= hi1:
            chips.append(1)
        elif lo2 <= p.pulse_us <= hi2:
            chips += [1, 1]
        elif p.pulse_us > hi2:
            break
        else:
            return None

        if p.gap_us < lo1:
            pass
        elif lo1 <= p.gap_us <= hi1:
            chips.append(0)
        elif lo2 <= p.gap_us <= hi2:
            chips += [0, 0]
        elif p.gap_us > hi2:
            break
        else:
            return None

    bits: list[int] = []
    i = 0
    while i + 1 < len(chips):
        h, l = chips[i], chips[i + 1]
        if h == 1 and l == 0:
            bits.append(0 if inverted else 1)
            i += 2
        elif h == 0 and l == 1:
            bits.append(1 if inverted else 0)
            i += 2
        else:
            return None

    return bits or None


def crc16(data: bytes, poly: int = 0x8005, init: int = 0x0000, ref_in: bool = True, ref_out: bool = True) -> int:
    """CRC-16 with configurable polynomial, init, and reflection."""
    crc = init
    for byte in data:
        if ref_in:
            byte = int(f"{byte:08b}"[::-1], 2)
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    if ref_out:
        crc = int(f"{crc:016b}"[::-1], 2)
    return crc


def bits_to_int(bits: list[int] | np.ndarray, msb_first: bool = True) -> int:
    seq = bits if msb_first else list(reversed(list(bits)))
    result = 0
    for b in seq:
        result = (result << 1) | int(b)
    return result


def crc8(data: bytes, poly: int = 0x31, init: int = 0x00) -> int:
    crc = init
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ poly) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def checksum_sum(data: bytes, mask: int = 0xFF) -> int:
    return sum(data) & mask
