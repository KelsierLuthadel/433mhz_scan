"""GPS location provider  reads NMEA 0183 sentences from a serial GPS receiver.

Typical USB GPS dongles appear as:
  Windows : COM3, COM4, …
  Linux   : /dev/ttyUSB0, /dev/ttyACM0
  macOS   : /dev/cu.usbmodem…

Usage:
    gps = GPSReader("COM3")
    gps.start()
    fix = gps.fix          # GPSFix | None
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class GPSFix:
    lat: float              # decimal degrees, positive = North
    lon: float              # decimal degrees, positive = East
    alt_m: float | None = None
    speed_knots: float | None = None
    heading: float | None = None
    satellites: int | None = None

    @property
    def lat_str(self) -> str:
        d = abs(self.lat)
        return f"{d:.6f}°{'N' if self.lat >= 0 else 'S'}"

    @property
    def lon_str(self) -> str:
        d = abs(self.lon)
        return f"{d:.6f}°{'E' if self.lon >= 0 else 'W'}"

    def as_dict(self) -> dict:
        d: dict = {"lat": self.lat, "lon": self.lon}
        if self.alt_m is not None:
            d["alt_m"] = self.alt_m
        if self.satellites is not None:
            d["satellites"] = self.satellites
        return d


# ---------------------------------------------------------------------------
# NMEA helpers
# ---------------------------------------------------------------------------

def _nmea_to_decimal(value: str, direction: str) -> float:
    """Convert NMEA ddmm.mmmm / dddmm.mmmm + N/S/E/W to signed decimal degrees."""
    if not value:
        return 0.0
    dot = value.index(".")
    degrees = int(value[:dot - 2])
    minutes = float(value[dot - 2:])
    decimal = degrees + minutes / 60.0
    if direction in ("S", "W"):
        decimal = -decimal
    return decimal


def _checksum_ok(sentence: str) -> bool:
    """Verify NMEA XOR checksum (after the * marker)."""
    if "*" not in sentence:
        return True
    body, chk_str = sentence[1:].rsplit("*", 1)
    expected = 0
    for ch in body:
        expected ^= ord(ch)
    try:
        return expected == int(chk_str[:2], 16)
    except ValueError:
        return False


def _parse_gprmc(fields: list[str]) -> GPSFix | None:
    """$GPRMC,hhmmss,status,lat,N/S,lon,E/W,speed,heading,date,...

    fields[0] is the sentence tag ($GPRMC / $GNRMC).
    """
    if len(fields) < 8 or fields[2] != "A":   # fields[2] = status A=active
        return None
    try:
        lat = _nmea_to_decimal(fields[3], fields[4])
        lon = _nmea_to_decimal(fields[5], fields[6])
        speed = float(fields[7]) if fields[7] else None
        heading = float(fields[8]) if len(fields) > 8 and fields[8] else None
        return GPSFix(lat=lat, lon=lon, speed_knots=speed, heading=heading)
    except (ValueError, IndexError):
        return None


def _parse_gpgga(fields: list[str]) -> GPSFix | None:
    """$GPGGA,hhmmss,lat,N/S,lon,E/W,quality,sats,hdop,alt,M,...

    fields[0] is the sentence tag ($GPGGA / $GNGGA).
    """
    if len(fields) < 10 or not fields[6] or fields[6] == "0":
        return None
    try:
        lat = _nmea_to_decimal(fields[2], fields[3])
        lon = _nmea_to_decimal(fields[4], fields[5])
        sats = int(fields[7]) if fields[7] else None
        alt = float(fields[9]) if fields[9] else None
        return GPSFix(lat=lat, lon=lon, alt_m=alt, satellites=sats)
    except (ValueError, IndexError):
        return None


def _parse_sentence(line: str) -> GPSFix | None:
    """Parse one NMEA sentence; return a GPSFix if it carries a valid position."""
    if not line.startswith("$"):
        return None
    if not _checksum_ok(line):
        return None
    # Strip checksum for field splitting
    body = line.split("*")[0]
    parts = body.split(",")
    tag = parts[0].lstrip("$").upper()

    if tag in ("GPRMC", "GNRMC"):
        return _parse_gprmc(parts)
    if tag in ("GPGGA", "GNGGA"):
        return _parse_gpgga(parts)
    return None


# ---------------------------------------------------------------------------
# GPSReader  background serial reader
# ---------------------------------------------------------------------------

class GPSReader:
    """Background thread that maintains the latest GPS fix from a serial device."""

    def __init__(self, port: str, baud: int = 9600) -> None:
        self._port = port
        self._baud = baud
        self._fix: GPSFix | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start reading in a daemon thread (non-blocking)."""
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="gps-reader"
        )
        self._thread.start()
        log.info("GPS reader started on %s at %d baud", self._port, self._baud)

    def stop(self) -> None:
        """Signal the reader thread to exit."""
        self._stop.set()

    @property
    def fix(self) -> GPSFix | None:
        """Return the latest valid GPS fix, or None if no fix yet."""
        with self._lock:
            return self._fix

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _run(self) -> None:
        try:
            import serial  # pyserial  imported lazily to keep module importable without it
        except ImportError:
            log.error("pyserial not installed  GPS disabled. Install with: pip install pyserial")
            return

        try:
            with serial.Serial(self._port, self._baud, timeout=1.0) as ser:
                log.info("GPS: opened %s", self._port)
                while not self._stop.is_set():
                    try:
                        raw = ser.readline()
                        line = raw.decode("ascii", errors="ignore").strip()
                    except Exception:
                        continue

                    fix = _parse_sentence(line)
                    if fix is None:
                        continue

                    with self._lock:
                        existing = self._fix
                        # Prefer a fix that includes altitude; otherwise always update.
                        if existing is None or fix.alt_m is not None or existing.alt_m is None:
                            self._fix = fix
                            log.debug("GPS fix: %s %s", fix.lat_str, fix.lon_str)

        except Exception as exc:
            log.error("GPS reader error on %s: %s", self._port, exc)
