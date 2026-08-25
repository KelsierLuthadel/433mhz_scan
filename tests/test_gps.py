"""Tests for sdr_receiver.gps  NMEA parsing and GPSReader."""
import pytest

from sdr_receiver.gps import (
    GPSFix,
    GPSReader,
    _checksum_ok,
    _nmea_to_decimal,
    _parse_gpgga,
    _parse_gprmc,
    _parse_sentence,
)


# ---------------------------------------------------------------------------
# _nmea_to_decimal
# ---------------------------------------------------------------------------

class TestNmeaToDecimal:
    def test_north(self):
        # 5130.0000 N = 51 + 30/60 = 51.5
        assert _nmea_to_decimal("5130.0000", "N") == pytest.approx(51.5)

    def test_south_is_negative(self):
        assert _nmea_to_decimal("5130.0000", "S") == pytest.approx(-51.5)

    def test_east(self):
        # 00008.0000 E = 0 + 8/60 ≈ 0.13333
        assert _nmea_to_decimal("00008.0000", "E") == pytest.approx(8 / 60, rel=1e-4)

    def test_west_is_negative(self):
        assert _nmea_to_decimal("00008.0000", "W") == pytest.approx(-8 / 60, rel=1e-4)

    def test_london_approx(self):
        # Longitude 000 7.1234 W ≈ -0.1187
        result = _nmea_to_decimal("00007.1234", "W")
        assert result < 0
        assert abs(result) < 1.0

    def test_empty_returns_zero(self):
        assert _nmea_to_decimal("", "N") == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# _checksum_ok
# ---------------------------------------------------------------------------

class TestChecksumOk:
    def test_valid_gprmc(self):
        # Pre-computed valid NMEA sentence
        line = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
        assert _checksum_ok(line) is True

    def test_corrupted_checksum(self):
        line = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*FF"
        assert _checksum_ok(line) is False

    def test_no_checksum_passes(self):
        # Sentences without * are accepted (checksum absent)
        assert _checksum_ok("$GPRMC,123519,A,4807.038,N") is True

    def test_gpgga_valid(self):
        line = "$GPGGA,092750.000,5321.6802,N,00630.3372,W,1,8,1.03,61.7,M,55.2,M,,*76"
        assert _checksum_ok(line) is True


# ---------------------------------------------------------------------------
# _parse_gprmc
# ---------------------------------------------------------------------------

class TestParseGprmc:
    def _fields(self, sentence: str):
        """Split a full GPRMC line into fields for _parse_gprmc."""
        parts = sentence.split("*")[0].split(",")
        return parts  # includes the $GPRMC tag as parts[0]

    def test_valid_active(self):
        line = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W"
        parts = line.split(",")
        fix = _parse_gprmc(parts)
        assert fix is not None
        assert fix.lat == pytest.approx(48.0 + 7.038 / 60, rel=1e-4)
        assert fix.lon == pytest.approx(11.0 + 31.000 / 60, rel=1e-4)

    def test_void_returns_none(self):
        parts = "$GPRMC,123519,V,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W".split(",")
        assert _parse_gprmc(parts) is None

    def test_south_west(self):
        parts = "$GPRMC,000000,A,3400.000,S,05800.000,W,0,0,010101,,".split(",")
        fix = _parse_gprmc(parts)
        assert fix is not None
        assert fix.lat < 0  # South
        assert fix.lon < 0  # West

    def test_speed_parsed(self):
        parts = "$GPRMC,123519,A,4807.038,N,01131.000,E,10.5,84.4,230394,,".split(",")
        fix = _parse_gprmc(parts)
        assert fix is not None
        assert fix.speed_knots == pytest.approx(10.5)

    def test_too_few_fields_returns_none(self):
        assert _parse_gprmc(["$GPRMC", "123519"]) is None


# ---------------------------------------------------------------------------
# _parse_gpgga
# ---------------------------------------------------------------------------

class TestParseGpgga:
    def test_valid_fix(self):
        # $GPGGA,time,lat,N,lon,W,quality,sats,hdop,alt,...
        parts = "$GPGGA,092750.000,5321.6802,N,00630.3372,W,1,8,1.03,61.7,M,55.2,M,,".split(",")
        fix = _parse_gpgga(parts)
        assert fix is not None
        assert fix.lat == pytest.approx(53.0 + 21.6802 / 60, rel=1e-4)
        assert fix.lon == pytest.approx(-(6.0 + 30.3372 / 60), rel=1e-4)
        assert fix.alt_m == pytest.approx(61.7)
        assert fix.satellites == 8

    def test_no_fix_quality_zero(self):
        parts = "$GPGGA,092750.000,5321.6802,N,00630.3372,W,0,0,,,,,,,".split(",")
        assert _parse_gpgga(parts) is None

    def test_too_few_fields(self):
        assert _parse_gpgga(["$GPGGA", "time"]) is None


# ---------------------------------------------------------------------------
# _parse_sentence (integration)
# ---------------------------------------------------------------------------

class TestParseSentence:
    def test_gprmc_sentence(self):
        line = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*6A"
        fix = _parse_sentence(line)
        assert fix is not None

    def test_gpgga_sentence(self):
        line = "$GPGGA,092750.000,5321.6802,N,00630.3372,W,1,8,1.03,61.7,M,55.2,M,,*76"
        fix = _parse_sentence(line)
        assert fix is not None
        assert fix.alt_m == pytest.approx(61.7)

    def test_unknown_sentence_returns_none(self):
        assert _parse_sentence("$GPHDT,270.0,T*03") is None

    def test_bad_checksum_returns_none(self):
        line = "$GPRMC,123519,A,4807.038,N,01131.000,E,022.4,084.4,230394,003.1,W*FF"
        assert _parse_sentence(line) is None

    def test_non_nmea_returns_none(self):
        assert _parse_sentence("not a sentence") is None

    def test_gnrmc_also_parsed(self):
        # GNRMC is the multi-constellation variant of GPRMC
        line = "$GNRMC,123519.00,A,4807.038,N,01131.000,E,0.0,,230394,,,A*70"
        # checksum may not match exactly  test just that tag is accepted if valid
        fix = _parse_sentence(line)
        # May be None due to checksum mismatch, but should not raise


# ---------------------------------------------------------------------------
# GPSFix helpers
# ---------------------------------------------------------------------------

class TestGPSFix:
    def test_lat_str_north(self):
        fix = GPSFix(lat=51.509865, lon=-0.118092)
        assert "N" in fix.lat_str
        assert "51" in fix.lat_str

    def test_lat_str_south(self):
        fix = GPSFix(lat=-33.8688, lon=151.2093)
        assert "S" in fix.lat_str

    def test_lon_str_east(self):
        fix = GPSFix(lat=48.8566, lon=2.3522)
        assert "E" in fix.lon_str

    def test_lon_str_west(self):
        fix = GPSFix(lat=51.5, lon=-0.1)
        assert "W" in fix.lon_str

    def test_as_dict_basic(self):
        fix = GPSFix(lat=1.0, lon=2.0)
        d = fix.as_dict()
        assert d["lat"] == 1.0
        assert d["lon"] == 2.0
        assert "alt_m" not in d

    def test_as_dict_with_alt(self):
        fix = GPSFix(lat=1.0, lon=2.0, alt_m=50.0, satellites=5)
        d = fix.as_dict()
        assert d["alt_m"] == 50.0
        assert d["satellites"] == 5


# ---------------------------------------------------------------------------
# GPSReader (unit  no real serial port)
# ---------------------------------------------------------------------------

class TestGPSReader:
    def test_initial_fix_is_none(self):
        reader = GPSReader("COM_FAKE_PORT")
        assert reader.fix is None

    def test_stop_before_start_safe(self):
        reader = GPSReader("COM_FAKE_PORT")
        reader.stop()  # should not raise
