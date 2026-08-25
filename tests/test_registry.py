"""Tests for the DEVICE_REGISTRY  loading, completeness, and try_decode."""
import pytest

from sdr_receiver.dsp import Pulse
from sdr_receiver.devices import DEVICE_REGISTRY, try_decode


NOISE_PULSES = [Pulse(pulse_us=100 + i * 13, gap_us=50 + i * 7) for i in range(10)]


class TestRegistryLoads:
    def test_registry_is_list(self):
        assert isinstance(DEVICE_REGISTRY, list)

    def test_registry_non_empty(self):
        assert len(DEVICE_REGISTRY) > 0

    def test_registry_has_at_least_300_decoders(self):
        assert len(DEVICE_REGISTRY) >= 300

    def test_all_entries_have_decode_method(self):
        for decoder in DEVICE_REGISTRY:
            assert callable(getattr(decoder, "decode", None)), (
                f"{decoder!r} is missing a decode() method"
            )

    def test_all_entries_have_name(self):
        for decoder in DEVICE_REGISTRY:
            name = getattr(decoder, "name", None)
            assert isinstance(name, str) and len(name) > 0, (
                f"{decoder!r} has a missing or empty name"
            )

    def test_no_duplicate_registry_entries(self):
        ids = [id(d) for d in DEVICE_REGISTRY]
        assert len(ids) == len(set(ids)), "Duplicate decoder instance in DEVICE_REGISTRY"


class TestTryDecode:
    def test_empty_pulses_returns_none(self):
        assert try_decode([], 433.92e6) is None

    def test_noise_returns_none(self):
        assert try_decode(NOISE_PULSES, 433.92e6) is None

    def test_returns_decoded_packet_or_none(self):
        from sdr_receiver.packet import DecodedPacket
        result = try_decode(NOISE_PULSES, 433.92e6)
        assert result is None or isinstance(result, DecodedPacket)


class TestRegistryCategories:
    """Verify at least one decoder from each category is registered."""

    EXPECTED_NAMES = [
        # security
        "Yale-HSA",
        # smart home
        "Somfy-RTS",
        # weather  nexus
        "Nexus-TH",
        # weather  lacrosse
        "LaCrosse-TX",
        # weather  acurite
        "Acurite-TH",
        # weather  fineoffset
        "Fine Offset WH1080",
        # tpms
        "GM-TPMS",
        "TyreGuard400",
        # car remotes
        "Ford Car Key",
        # power
        "Efergy-E2-Classic",
        # water meters
        "Neptune-R900",
        # bbq/pool/rain
        "Maverick-ET73",
        # misc
        "Generic-Remote",
        # missing/late additions
        "Biltema-Rain-Gauge",
    ]

    def test_expected_names_registered(self):
        registered = {d.name for d in DEVICE_REGISTRY}
        for name in self.EXPECTED_NAMES:
            assert name in registered, f"Expected decoder '{name}' not found in DEVICE_REGISTRY"


class TestRegistryOrder:
    def test_legacy_decoders_first(self):
        # The legacy NexusTH, FineOffsetWH2, Acurite609 should be near the top
        first_ten_names = [d.name for d in DEVICE_REGISTRY[:10]]
        # At least one legacy name should appear in the first 10
        legacy = {"Nexus-TH", "Fine-Offset-WH2", "Acurite-609TXC"}
        assert any(n in legacy for n in first_ten_names), (
            f"No legacy decoder in first 10 entries: {first_ten_names}"
        )
