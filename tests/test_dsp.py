"""Tests for sdr_receiver.dsp  signal processing primitives."""
import numpy as np
import pytest

from sdr_receiver.dsp import (
    Pulse,
    bits_to_int,
    checksum_sum,
    crc8,
    crc16,
    demodulate_ook,
    extract_packets,
    pulses_to_bits_manchester,
    pulses_to_bits_pcm,
    pulses_to_bits_ppm,
    pulses_to_bits_pwm,
)


# ---------------------------------------------------------------------------
# bits_to_int
# ---------------------------------------------------------------------------

class TestBitsToInt:
    def test_zero(self):
        assert bits_to_int([0, 0, 0, 0]) == 0

    def test_one(self):
        assert bits_to_int([0, 0, 0, 1]) == 1

    def test_msb_first(self):
        # 0b1010 = 10
        assert bits_to_int([1, 0, 1, 0]) == 10

    def test_lsb_first(self):
        # LSB-first [1,0,1,0] = 0b0101 = 5
        assert bits_to_int([1, 0, 1, 0], msb_first=False) == 5

    def test_eight_bits(self):
        assert bits_to_int([1, 1, 1, 1, 1, 1, 1, 1]) == 255

    def test_single_bit_one(self):
        assert bits_to_int([1]) == 1

    def test_single_bit_zero(self):
        assert bits_to_int([0]) == 0


# ---------------------------------------------------------------------------
# crc8
# ---------------------------------------------------------------------------

class TestCrc8:
    def test_empty_default(self):
        # CRC8 of empty data with poly=0x31, init=0x00 is 0
        assert crc8(b"", poly=0x31, init=0x00) == 0x00

    def test_known_value(self):
        # CRC-8/MAXIM (poly=0x31, init=0x00): 0x31 is a well-known poly
        # crc8([0x00]) with poly=0x07, init=0x00 is 0x00
        assert crc8(b"\x00", poly=0x07, init=0x00) == 0x00

    def test_all_zeros_poly07(self):
        assert crc8(b"\x00\x00\x00", poly=0x07, init=0x00) == 0x00

    def test_self_check(self):
        # Appending the CRC to the data should give a predictable result
        data = b"\x01\x02\x03\x04"
        c = crc8(data, poly=0x31, init=0x00)
        # Recalculating on same data gives same value
        assert crc8(data, poly=0x31, init=0x00) == c

    def test_different_data_different_crc(self):
        a = crc8(b"\x01", poly=0x31, init=0x00)
        b = crc8(b"\x02", poly=0x31, init=0x00)
        assert a != b

    def test_init_affects_result(self):
        data = b"\xAA\xBB"
        c0 = crc8(data, poly=0x31, init=0x00)
        cFF = crc8(data, poly=0x31, init=0xFF)
        assert c0 != cFF


# ---------------------------------------------------------------------------
# crc16
# ---------------------------------------------------------------------------

class TestCrc16:
    def test_empty(self):
        assert crc16(b"", poly=0x8005, init=0x0000) == 0x0000

    def test_reproducible(self):
        data = b"\x10\x20\x30"
        assert crc16(data) == crc16(data)

    def test_different_poly(self):
        data = b"\xAA\xBB\xCC"
        c1 = crc16(data, poly=0x8005)
        c2 = crc16(data, poly=0x1021)
        assert c1 != c2

    def test_known_ccitt_false(self):
        # CRC-16/CCITT-FALSE: poly=0x1021, init=0xFFFF, refIn=False, refOut=False
        # "123456789" → 0x29B1
        result = crc16(
            b"123456789",
            poly=0x1021,
            init=0xFFFF,
            ref_in=False,
            ref_out=False,
        )
        assert result == 0x29B1


# ---------------------------------------------------------------------------
# checksum_sum
# ---------------------------------------------------------------------------

class TestChecksumSum:
    def test_zero(self):
        assert checksum_sum(b"\x00\x00\x00") == 0

    def test_simple(self):
        assert checksum_sum(b"\x01\x02\x03") == 6

    def test_wraps_at_ff(self):
        # 0xFF + 0x01 = 0x100, masked to 0x00
        assert checksum_sum(b"\xFF\x01") == 0x00

    def test_custom_mask(self):
        # sum of [0x10, 0x20] = 0x30; mask 0x0F → 0x00
        assert checksum_sum(b"\x10\x20", mask=0x0F) == 0x00


# ---------------------------------------------------------------------------
# pulses_to_bits_pwm
# ---------------------------------------------------------------------------

class TestPulsesToBitsPWM:
    SHORT = 500.0
    LONG = 1000.0

    def _p(self, pulse_us: float) -> Pulse:
        return Pulse(pulse_us=pulse_us, gap_us=200.0)

    def test_all_zeros(self):
        pulses = [self._p(500)] * 4
        bits = pulses_to_bits_pwm(pulses, self.SHORT, self.LONG)
        assert bits == [0, 0, 0, 0]

    def test_all_ones(self):
        pulses = [self._p(1000)] * 4
        bits = pulses_to_bits_pwm(pulses, self.SHORT, self.LONG)
        assert bits == [1, 1, 1, 1]

    def test_mixed(self):
        pulses = [self._p(500), self._p(1000), self._p(500), self._p(1000)]
        bits = pulses_to_bits_pwm(pulses, self.SHORT, self.LONG)
        assert bits == [0, 1, 0, 1]

    def test_within_tolerance(self):
        # 500 ± 45% → 275 to 725
        pulses = [self._p(700)]  # within tolerance of 500
        bits = pulses_to_bits_pwm(pulses, self.SHORT, self.LONG)
        assert bits == [0]

    def test_ambiguous_returns_none(self):
        # 200 < short_min (500 * 0.55 = 275)  outside both short and long ranges
        pulses = [self._p(200)]
        bits = pulses_to_bits_pwm(pulses, self.SHORT, self.LONG)
        assert bits is None

    def test_empty_returns_empty(self):
        assert pulses_to_bits_pwm([], self.SHORT, self.LONG) == []


# ---------------------------------------------------------------------------
# pulses_to_bits_ppm
# ---------------------------------------------------------------------------

class TestPulsesToBitsPPM:
    SHORT = 500.0
    LONG = 1000.0

    def _p(self, gap_us: float) -> Pulse:
        return Pulse(pulse_us=200.0, gap_us=gap_us)

    def test_all_zeros(self):
        pulses = [self._p(500)] * 4
        bits = pulses_to_bits_ppm(pulses, self.SHORT, self.LONG)
        assert bits == [0, 0, 0, 0]

    def test_all_ones(self):
        pulses = [self._p(1000)] * 4
        bits = pulses_to_bits_ppm(pulses, self.SHORT, self.LONG)
        assert bits == [1, 1, 1, 1]

    def test_mixed(self):
        pulses = [self._p(500), self._p(1000), self._p(500)]
        bits = pulses_to_bits_ppm(pulses, self.SHORT, self.LONG)
        assert bits == [0, 1, 0]

    def test_bad_gap_returns_none(self):
        # 200 < short_min (500 * 0.55 = 275)  outside both short and long ranges
        pulses = [self._p(200)]
        bits = pulses_to_bits_ppm(pulses, self.SHORT, self.LONG)
        assert bits is None


# ---------------------------------------------------------------------------
# pulses_to_bits_pcm
# ---------------------------------------------------------------------------

class TestPulsesToBitsPCM:
    CHIP = 500.0

    def test_single_chip_high_low(self):
        # One chip high + one chip low → [1, 0]
        pulses = [Pulse(pulse_us=500, gap_us=500)]
        bits = pulses_to_bits_pcm(pulses, self.CHIP)
        assert bits == [1, 0]

    def test_double_high(self):
        # Two chips high + one low → [1, 1, 0]
        pulses = [Pulse(pulse_us=1000, gap_us=500)]
        bits = pulses_to_bits_pcm(pulses, self.CHIP)
        assert bits == [1, 1, 0]

    def test_inverted(self):
        pulses = [Pulse(pulse_us=500, gap_us=500)]
        bits = pulses_to_bits_pcm(pulses, self.CHIP, inverted=True)
        assert bits == [0, 1]

    def test_bad_pulse_returns_none(self):
        # 200 rounds to 0 chips (n_high < 1)  too short to form even one chip
        pulses = [Pulse(pulse_us=200, gap_us=500)]
        bits = pulses_to_bits_pcm(pulses, self.CHIP)
        assert bits is None

    def test_empty_returns_none(self):
        # Empty input → no chips → None
        assert pulses_to_bits_pcm([], self.CHIP) is None


# ---------------------------------------------------------------------------
# pulses_to_bits_manchester
# ---------------------------------------------------------------------------

class TestPulsesToBitsManchester:
    CHIP = 500.0

    def test_all_ones(self):
        # Each Pulse(500, 500) produces chips [1, 0] → bit 1
        pulses = [Pulse(pulse_us=500, gap_us=500)] * 3
        bits = pulses_to_bits_manchester(pulses, self.CHIP)
        assert bits == [1, 1, 1]

    def test_one_then_zero(self):
        # bits [1, 0]: chips [1,0,0,1]
        # Pulse(500, 1000) → chips [1, 0, 0]
        # Pulse(500, 500)  → chips [1, 0, 0, 1, 0]
        # pairs: (1,0)→1, (0,1)→0  ✓
        pulses = [Pulse(500, 1000), Pulse(500, 500)]
        bits = pulses_to_bits_manchester(pulses, self.CHIP)
        assert bits == [1, 0]

    def test_inverted(self):
        # inverted=True: [1,0]=0 and [0,1]=1
        pulses = [Pulse(500, 500)] * 2
        bits = pulses_to_bits_manchester(pulses, self.CHIP, inverted=True)
        assert bits == [0, 0]

    def test_bad_chip_returns_none(self):
        # 200 < chip_min (500 * 0.55 = 275)  below single-chip lower bound → None
        pulses = [Pulse(pulse_us=200, gap_us=200)]
        bits = pulses_to_bits_manchester(pulses, self.CHIP)
        assert bits is None

    def test_empty_returns_none(self):
        assert pulses_to_bits_manchester([], self.CHIP) is None


# ---------------------------------------------------------------------------
# extract_packets
# ---------------------------------------------------------------------------

class TestExtractPackets:
    def _make(self, gap_us: float) -> Pulse:
        return Pulse(pulse_us=500.0, gap_us=gap_us)

    def test_single_packet(self):
        # 8 short pulses then a reset gap
        pulses = [self._make(200)] * 8 + [self._make(10_000)]
        packets = extract_packets(pulses, reset_us=8_000)
        assert len(packets) == 1
        assert len(packets[0]) == 9  # includes the reset-gap pulse

    def test_two_packets(self):
        short = [self._make(200)] * 8
        sep = [self._make(10_000)]
        pulses = short + sep + short + sep
        packets = extract_packets(pulses, reset_us=8_000)
        assert len(packets) == 2

    def test_minimum_pulses_filter(self):
        # Only 4 pulses before reset  below min_pulses=8 → discarded
        pulses = [self._make(200)] * 4 + [self._make(10_000)]
        packets = extract_packets(pulses, reset_us=8_000, min_pulses=8)
        assert len(packets) == 0

    def test_trailing_pulses_included(self):
        # Pulses with no terminal reset gap are still emitted
        pulses = [self._make(200)] * 8
        packets = extract_packets(pulses, reset_us=8_000)
        assert len(packets) == 1


# ---------------------------------------------------------------------------
# demodulate_ook (integration-level)
# ---------------------------------------------------------------------------

class TestDemodulateOOK:
    SAMPLE_RATE = 250_000

    def test_silent_returns_empty(self):
        samples = np.zeros(4096, dtype=np.complex64)
        pulses = demodulate_ook(samples, self.SAMPLE_RATE)
        assert pulses == []

    def test_too_short_returns_empty(self):
        samples = np.zeros(4, dtype=np.complex64)
        pulses = demodulate_ook(samples, self.SAMPLE_RATE)
        assert pulses == []

    def test_square_wave_produces_pulses(self):
        # Synthetic: 500 µs ON / 500 µs OFF at 250 kHz → 125 samples each
        sps = self.SAMPLE_RATE
        chip_samples = int(sps * 500e-6)  # 125
        n_chips = 20
        amplitude = np.ones(chip_samples, dtype=np.float32)
        silence = np.zeros(chip_samples, dtype=np.float32)
        mag = np.tile(np.concatenate([amplitude, silence]), n_chips).astype(np.complex64)
        pulses = demodulate_ook(mag, sps)
        assert len(pulses) > 0
        # Each pulse should be ~500 µs
        for p in pulses:
            assert 200 < p.pulse_us < 800
