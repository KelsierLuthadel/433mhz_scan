from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class DecodedPacket:
    time: datetime
    model: str
    frequency: float | None  # Hz
    raw: dict[str, Any]

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_fields(
        cls,
        model: str,
        freq_hz: float | None,
        fields: dict[str, Any],
    ) -> "DecodedPacket":
        """Build a packet from a device decoder result."""
        now = datetime.now()
        raw: dict[str, Any] = {"time": now.isoformat(), "model": model}
        if freq_hz is not None:
            raw["freq"] = freq_hz
        raw.update(fields)
        return cls(time=now, model=model, frequency=freq_hz, raw=raw)

    def stamp_location(self, fix: "Any") -> None:
        """Attach a GPSFix to this packet's raw dict (called after construction)."""
        if fix is None:
            return
        self.raw["lat"] = fix.lat
        self.raw["lon"] = fix.lon
        if fix.alt_m is not None:
            self.raw["alt_m"] = fix.alt_m
        if fix.satellites is not None:
            self.raw["gps_satellites"] = fix.satellites

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "DecodedPacket":
        """Build a packet from an rtl_433-style JSON dict (kept for compatibility)."""
        time_str = data.get("time", "")
        try:
            ts = datetime.fromisoformat(time_str)
        except (ValueError, TypeError):
            ts = datetime.now()

        freq = data.get("freq") or data.get("frequency")
        if freq is not None:
            try:
                freq = float(freq)
            except (ValueError, TypeError):
                freq = None

        return cls(time=ts, model=data.get("model", "Unknown"), frequency=freq, raw=data)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def freq_mhz(self) -> str:
        if self.frequency is None:
            return "?"
        return f"{self.frequency / 1e6:.3f} MHz"

    def summary_fields(self) -> dict[str, Any]:
        skip = {"time", "model", "freq", "frequency", "protocol", "rssi", "snr", "noise"}
        return {k: v for k, v in self.raw.items() if k not in skip}
