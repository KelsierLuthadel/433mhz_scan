"""Tests for sdr_receiver.packet  DecodedPacket data model."""
import pytest
from datetime import datetime

from sdr_receiver.packet import DecodedPacket


class TestFromFields:
    def test_basic_fields_present(self):
        pkt = DecodedPacket.from_fields("TestDevice", 433.92e6, {"temperature_C": 21.5})
        assert pkt.model == "TestDevice"
        assert pkt.frequency == 433.92e6
        assert pkt.raw["model"] == "TestDevice"
        assert pkt.raw["temperature_C"] == 21.5

    def test_freq_in_raw(self):
        pkt = DecodedPacket.from_fields("X", 915e6, {})
        assert pkt.raw["freq"] == 915e6

    def test_no_freq(self):
        pkt = DecodedPacket.from_fields("X", None, {"id": 42})
        assert pkt.frequency is None
        assert "freq" not in pkt.raw
        assert pkt.raw["id"] == 42

    def test_time_is_isoformat(self):
        pkt = DecodedPacket.from_fields("X", None, {})
        ts = pkt.raw["time"]
        # Should parse without error
        datetime.fromisoformat(ts)

    def test_fields_override_nothing(self):
        # Extra fields don't shadow model/time
        pkt = DecodedPacket.from_fields("Dev", 433e6, {"humidity": 55, "battery_ok": True})
        assert pkt.raw["humidity"] == 55
        assert pkt.raw["battery_ok"] is True
        assert pkt.raw["model"] == "Dev"


class TestFromJson:
    def test_basic(self):
        data = {"time": "2026-01-01T12:00:00", "model": "Test", "freq": 433920000.0}
        pkt = DecodedPacket.from_json(data)
        assert pkt.model == "Test"
        assert pkt.frequency == 433920000.0

    def test_bad_time_falls_back(self):
        data = {"time": "not-a-date", "model": "X"}
        pkt = DecodedPacket.from_json(data)
        # Should not raise; time should be close to now
        assert isinstance(pkt.time, datetime)

    def test_missing_time(self):
        data = {"model": "X"}
        pkt = DecodedPacket.from_json(data)
        assert isinstance(pkt.time, datetime)

    def test_missing_model(self):
        data = {"time": "2026-01-01T00:00:00"}
        pkt = DecodedPacket.from_json(data)
        assert pkt.model == "Unknown"

    def test_frequency_alternatives(self):
        data = {"model": "X", "frequency": 433.92e6}
        pkt = DecodedPacket.from_json(data)
        assert pkt.frequency == 433.92e6

    def test_frequency_none_on_bad_value(self):
        data = {"model": "X", "freq": "bad"}
        pkt = DecodedPacket.from_json(data)
        assert pkt.frequency is None


class TestFreqMhz:
    def test_known_frequency(self):
        pkt = DecodedPacket.from_fields("X", 433920000.0, {})
        assert pkt.freq_mhz == "433.920 MHz"

    def test_none_frequency(self):
        pkt = DecodedPacket.from_fields("X", None, {})
        assert pkt.freq_mhz == "?"


class TestSummaryFields:
    def test_excludes_standard_keys(self):
        pkt = DecodedPacket.from_fields("Dev", 433e6, {"temperature_C": 20.0, "rssi": -70})
        summary = pkt.summary_fields()
        assert "time" not in summary
        assert "model" not in summary
        assert "freq" not in summary
        assert "rssi" not in summary
        assert summary["temperature_C"] == 20.0

    def test_includes_custom_keys(self):
        pkt = DecodedPacket.from_fields("Dev", None, {"id": "0xAB", "channel": 2})
        summary = pkt.summary_fields()
        assert summary["id"] == "0xAB"
        assert summary["channel"] == 2


class TestStampLocation:
    def _fix(self, lat=51.5, lon=-0.1, alt=12.3, sats=8):
        from sdr_receiver.gps import GPSFix
        return GPSFix(lat=lat, lon=lon, alt_m=alt, satellites=sats)

    def test_stamps_lat_lon(self):
        pkt = DecodedPacket.from_fields("X", None, {})
        pkt.stamp_location(self._fix(lat=48.8566, lon=2.3522))
        assert pkt.raw["lat"] == pytest.approx(48.8566)
        assert pkt.raw["lon"] == pytest.approx(2.3522)

    def test_stamps_altitude(self):
        pkt = DecodedPacket.from_fields("X", None, {})
        pkt.stamp_location(self._fix(alt=100.0))
        assert pkt.raw["alt_m"] == pytest.approx(100.0)

    def test_stamps_satellites(self):
        pkt = DecodedPacket.from_fields("X", None, {})
        pkt.stamp_location(self._fix(sats=6))
        assert pkt.raw["gps_satellites"] == 6

    def test_no_alt_key_when_none(self):
        from sdr_receiver.gps import GPSFix
        fix = GPSFix(lat=1.0, lon=2.0, alt_m=None)
        pkt = DecodedPacket.from_fields("X", None, {})
        pkt.stamp_location(fix)
        assert "alt_m" not in pkt.raw

    def test_none_fix_is_noop(self):
        pkt = DecodedPacket.from_fields("X", None, {"channel": 1})
        pkt.stamp_location(None)
        assert "lat" not in pkt.raw
        assert pkt.raw["channel"] == 1
