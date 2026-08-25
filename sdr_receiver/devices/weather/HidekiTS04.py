"""Hideki TS04 temperature/humidity/wind/rain sensor (and variants)."""
from __future__ import annotations
from ..base import RawDecoder
from ...packet import DecodedPacket


class HidekiTS04(RawDecoder):
    """Hideki TS04 temperature/humidity/wind/rain sensor (and variants).

    Modulation: OOK_PULSE_DMC (Differential Manchester Code)
    chip_us=520, long_us=1040, reset_us=4000
    DMC is not natively supported by OOK base classes; this is a stub.
    The full protocol encodes 8 data bits + 1 parity bit per group, with
    a sync header of 00000110 and XOR/CRC-8 verification.
    """

    name = "Hideki-TS04"

    def decode(self, pulses: list, freq_hz: float) -> DecodedPacket | None:  # type: ignore[override]
        return None


__all__ = ["HidekiTS04"]
