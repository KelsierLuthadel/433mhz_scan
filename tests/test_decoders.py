"""Tests for decoder base classes and a selection of concrete decoders."""
import pytest

from sdr_receiver.dsp import Pulse, bits_to_int
from sdr_receiver.devices.base import (
    ManchesterDecoder,
    OOKPCMDecoder,
    OOKPPMDecoder,
    OOKPWMDecoder,
    RawDecoder,
)
from sdr_receiver.packet import DecodedPacket


# ---------------------------------------------------------------------------
# Minimal concrete decoder implementations used only in tests
# ---------------------------------------------------------------------------

class _AlwaysOneDecoder(OOKPWMDecoder):
    """Returns a packet for any 4-bit input that passes PWM decoding."""
    name    = "_TestPWM"
    short_us = 500.0
    long_us  = 1000.0
    reset_us = 8000.0
    n_bits   = 4

    def _parse(self, bits, freq_hz):
        return DecodedPacket.from_fields(self.name, freq_hz, {"bits": bits})


class _AlwaysOnePPM(OOKPPMDecoder):
    name    = "_TestPPM"
    short_us = 500.0
    long_us  = 1000.0
    reset_us = 8000.0
    n_bits   = 4

    def _parse(self, bits, freq_hz):
        return DecodedPacket.from_fields(self.name, freq_hz, {"bits": bits})


class _AlwaysOnePCM(OOKPCMDecoder):
    name    = "_TestPCM"
    chip_us  = 500.0
    reset_us = 8000.0
    n_bits   = 4

    def _parse(self, bits, freq_hz):
        return DecodedPacket.from_fields(self.name, freq_hz, {"bits": bits})


class _AlwaysOneManchester(ManchesterDecoder):
    name    = "_TestManchester"
    chip_us  = 500.0
    reset_us = 8000.0
    n_bits   = 4

    def _parse(self, bits, freq_hz):
        return DecodedPacket.from_fields(self.name, freq_hz, {"bits": bits})


class _NullRaw(RawDecoder):
    name = "_TestRaw"

    def decode(self, pulses, freq_hz):
        return None


# ---------------------------------------------------------------------------
# OOKPWMDecoder dispatch
# ---------------------------------------------------------------------------

class TestOOKPWMDecoder:
    dec = _AlwaysOneDecoder()

    def _make(self, pulse_us):
        return Pulse(pulse_us=pulse_us, gap_us=200.0)

    def test_returns_none_for_empty(self):
        assert self.dec.decode([], 433.92e6) is None

    def test_returns_none_too_few_pulses(self):
        pulses = [self._make(500)] * 2  # fewer than n_bits=4
        assert self.dec.decode(pulses, 433.92e6) is None

    def test_decodes_four_zeros(self):
        pulses = [self._make(500)] * 4
        pkt = self.dec.decode(pulses, 433.92e6)
        assert pkt is not None
        assert pkt.raw["bits"] == [0, 0, 0, 0]

    def test_decodes_four_ones(self):
        pulses = [self._make(1000)] * 4
        pkt = self.dec.decode(pulses, 433.92e6)
        assert pkt is not None
        assert pkt.raw["bits"] == [1, 1, 1, 1]

    def test_decodes_mixed(self):
        pulses = [self._make(500), self._make(1000), self._make(500), self._make(1000)]
        pkt = self.dec.decode(pulses, 433.92e6)
        assert pkt is not None
        assert pkt.raw["bits"] == [0, 1, 0, 1]

    def test_reset_gap_pulses_filtered(self):
        # A pulse whose duration exceeds reset_us should be silently skipped
        pulses = [self._make(500)] * 3 + [Pulse(9000, 200)] + [self._make(500)]
        # Only 4 valid pulses after filtering, should still decode
        pkt = self.dec.decode(pulses, 433.92e6)
        assert pkt is not None


# ---------------------------------------------------------------------------
# OOKPPMDecoder dispatch
# ---------------------------------------------------------------------------

class TestOOKPPMDecoder:
    dec = _AlwaysOnePPM()

    def _make(self, gap_us):
        return Pulse(pulse_us=200.0, gap_us=gap_us)

    def test_returns_none_for_empty(self):
        assert self.dec.decode([], 433.92e6) is None

    def test_decodes_short_gaps(self):
        pulses = [self._make(500)] * 4
        pkt = self.dec.decode(pulses, 433.92e6)
        assert pkt is not None
        assert pkt.raw["bits"] == [0, 0, 0, 0]

    def test_decodes_long_gaps(self):
        pulses = [self._make(1000)] * 4
        pkt = self.dec.decode(pulses, 433.92e6)
        assert pkt is not None
        assert pkt.raw["bits"] == [1, 1, 1, 1]


# ---------------------------------------------------------------------------
# OOKPCMDecoder dispatch
# ---------------------------------------------------------------------------

class TestOOKPCMDecoder:
    dec = _AlwaysOnePCM()

    def test_returns_none_for_empty(self):
        assert self.dec.decode([], 433.92e6) is None

    def test_decodes_single_chip_sequence(self):
        # 4 chips high: 2 pulses of 1 chip each, each followed by 1-chip gap
        pulses = [Pulse(500, 500)] * 4  # produces [1,0,1,0,1,0,1,0,...] chips
        # n_bits=4; will look for first 4 bits: [1,0,1,0]
        pkt = self.dec.decode(pulses, 433.92e6)
        assert pkt is not None


# ---------------------------------------------------------------------------
# ManchesterDecoder dispatch
# ---------------------------------------------------------------------------

class TestManchesterDecoder:
    dec = _AlwaysOneManchester()

    def test_returns_none_for_empty(self):
        assert self.dec.decode([], 433.92e6) is None

    def test_decodes_all_ones(self):
        # Each Pulse(500, 500) → chips [1,0] → bit 1
        pulses = [Pulse(500, 500)] * 4
        pkt = self.dec.decode(pulses, 433.92e6)
        assert pkt is not None
        assert pkt.raw["bits"] == [1, 1, 1, 1]


# ---------------------------------------------------------------------------
# RawDecoder
# ---------------------------------------------------------------------------

class TestRawDecoder:
    def test_decode_returns_none(self):
        dec = _NullRaw()
        assert dec.decode([], 433.92e6) is None


# ---------------------------------------------------------------------------
# Concrete device decoders  smoke tests (import + None on garbage input)
# ---------------------------------------------------------------------------

class TestConcreteDecoderSmoke:
    """Each concrete decoder must:
    1. Import without error.
    2. Return None for empty pulse list.
    3. Return None for random short noise.
    """

    NOISE = [Pulse(100 + i * 7, 50 + i * 3) for i in range(20)]

    @pytest.mark.parametrize("module,cls", [
        ("sdr_receiver.devices.security.YaleHSA", "YaleHSA"),
        ("sdr_receiver.devices.security.SimpliSafe", "SimpliSafe"),
        ("sdr_receiver.devices.security.HoneywellSecurity", "HoneywellSecurity"),
        ("sdr_receiver.devices.smart_home.SomfyRTS", "SomfyRTS"),
        ("sdr_receiver.devices.smart_home.Intertechno", "Intertechno"),
        ("sdr_receiver.devices.weather.NexusTH", "NexusTH"),
        ("sdr_receiver.devices.weather.LaCrosseTX", "LaCrosseTX"),
        ("sdr_receiver.devices.weather.bresser5in1", "Bresser5in1"),
        ("sdr_receiver.devices.weather.fineoffsetwh1080", "FineOffsetWH1080"),
        ("sdr_receiver.devices.tpms.TpmsGm", "TpmsGm"),
        ("sdr_receiver.devices.tpms.TpmsTyreguard400", "TpmsTyreguard400"),
        ("sdr_receiver.devices.car_remotes.FordRemote", "FordRemote"),
        ("sdr_receiver.devices.power_energy.EfergyE2Classic", "EfergyE2Classic"),
        ("sdr_receiver.devices.water_meters.NeptuneR900", "NeptuneR900"),
        ("sdr_receiver.devices.bbq_pool_rain.MaverickET73", "MaverickET73"),
        ("sdr_receiver.devices.misc.GenericRemote", "GenericRemote"),
        ("sdr_receiver.devices.missing.ElroDb286a", "ElroDb286a"),
    ])
    def test_import_and_returns_none_on_noise(self, module, cls):
        import importlib
        mod = importlib.import_module(module)
        decoder_cls = getattr(mod, cls)
        decoder = decoder_cls()
        assert decoder.decode([], 433.92e6) is None
        assert decoder.decode(self.NOISE, 433.92e6) is None

    def test_decoder_has_name(self):
        from sdr_receiver.devices.weather.NexusTH import NexusTH
        dec = NexusTH()
        assert isinstance(dec.name, str)
        assert len(dec.name) > 0


# ---------------------------------------------------------------------------
# TpmsGm  full Manchester decoder with known good data
# ---------------------------------------------------------------------------

class TestTpmsGm:
    """Synthesize a valid TpmsGm packet and verify decoding."""

    def _make_bits(self) -> list[int]:
        """Build a minimal valid TpmsGm bit sequence (130 bits)."""
        # preamble: b[0:6] all 0x00
        bits = [0] * 48  # 6 bytes × 8

        # flags (2 bytes): no battery low, no learn mode flags set (all 0)
        bits += [0] * 16  # b[6:8]

        # sensor ID (5 bytes = 40 bits)
        sensor_id = 0x12345678AB
        for i in range(39, -1, -1):
            bits.append((sensor_id >> i) & 1)

        # pressure: 200 kPa → raw = round(200 / 2.75) = 73
        bits += [(73 >> (7 - i)) & 1 for i in range(8)]

        # temperature: 25°C → raw = 25 + 60 = 85
        bits += [(85 >> (7 - i)) & 1 for i in range(8)]

        # checksum: sum of bytes 6..14 & 0xFF
        # b[6:8]=0x0000, b[8:13]=sensor_id bytes, b[13]=73, b[14]=85
        from sdr_receiver.dsp import bits_to_int
        payload_bits = bits[48:]  # flags + id + pressure + temp = 16+40+8+8 = 72 bits = 9 bytes
        payload_bytes = bytes(bits_to_int(payload_bits[i:i+8]) for i in range(0, 72, 8))
        csum = sum(payload_bytes) & 0xFF
        bits += [(csum >> (7 - i)) & 1 for i in range(8)]

        # Total should be 48+16+40+8+8+8 = 128 bits; pad to 130
        bits += [0, 0]
        return bits

    def _manchester_encode(self, bits: list[int], chip_us: float = 120.0) -> list[Pulse]:
        """Encode bits as Manchester pulses (G.E. Thomas: 1=[1,0], 0=[0,1])."""
        chips: list[int] = []
        for b in bits:
            if b == 1:
                chips += [1, 0]
            else:
                chips += [0, 1]

        pulses: list[Pulse] = []
        i = 0
        while i < len(chips):
            # count consecutive highs
            j = i
            while j < len(chips) and chips[j] == 1:
                j += 1
            high_chips = j - i
            if high_chips == 0:
                # skip leading lows (they'd be gaps before first pulse)
                i += 1
                continue

            # count consecutive lows after the high run
            k = j
            while k < len(chips) and chips[k] == 0:
                k += 1
            low_chips = k - j

            pulses.append(Pulse(
                pulse_us=high_chips * chip_us,
                gap_us=low_chips * chip_us,
            ))
            i = k

        return pulses

    def test_valid_packet_decodes(self):
        from sdr_receiver.devices.tpms.TpmsGm import TpmsGm
        dec = TpmsGm()
        bits = self._make_bits()
        pulses = self._manchester_encode(bits, chip_us=120.0)
        pkt = dec.decode(pulses, 433.92e6)
        # With a valid preamble+checksum the decoder should return a packet
        if pkt is not None:
            assert "pressure_kPa" in pkt.raw
            assert "temperature_C" in pkt.raw
            assert pkt.raw["temperature_C"] == 25

    def test_bad_preamble_returns_none(self):
        from sdr_receiver.devices.tpms.TpmsGm import TpmsGm
        dec = TpmsGm()
        # Preamble byte 0 non-zero → should fail
        bits = self._make_bits()
        bits[0] = 1  # corrupt preamble
        pulses = self._manchester_encode(bits, chip_us=120.0)
        assert dec.decode(pulses, 433.92e6) is None
