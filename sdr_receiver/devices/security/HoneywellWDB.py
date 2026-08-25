"""Honeywell ActivLink, wireless door bell, PIR Motion sensor.

Copyright (C) 2018 Benjamin Larsson

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Honeywell ActivLink, wireless door bell, PIR Motion sensor.

Frame documentation courtesy of https://github.com/klohner/honeywell-wireless-doorbell
Updated to include Door/Window Contact sensor

Frame bits used in Honeywell RCWL300A, RCWL330A, Series 3, 5, 9 and all Decor Series:

Wireless Chimes

    0000 0000 1111 1111 2222 2222 3333 3333 4444 4444 5555 5555
    7654 3210 7654 3210 7654 3210 7654 3210 7654 3210 7654 3210
    XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XXXX XX.. XXX. .... KEY DATA (any change and receiver doesn't seem to
                                                                          recognize signal)
    XXXX XXXX XXXX XXXX XXXX .... .... .... .... .... .... .... KEY ID (different for each transmitter)
    .... .... .... .... .... 0000 0... 0000 0000 00.. 0... .... KEY UNKNOWN 0 (always 0 in devices I've tested)
    .... .... .... .... .... .... .XXX .... .... .... .... .... DEVICE TYPE (10 = doorbell, 01 = PIR Motion sensor,
                                                                            101 = door/window))
    .... .... .... .... .... .... .... .... .... ..XX .XXX XXX. FLAG DATA (may be modified for possible effects on
                                                                           receiver)
    .... .... .... .... .... .... .... .... .... ..XX .... .... ALERT (00 = normal, 01 or 10 = right-left halo light
                                                                       pattern, 11 = full volume alarm)
    .... .... .... .... .... .... .... .... .... .... .XX. .... DOOR/WINDOW (10 = Closed, 01 = Opened)
    .... .... .... .... .... .... .... .... .... .... ...X .... SECRET KNOCK (0 = default, 1 if doorbell is pressed 3x
                                                                              rapidly)
    .... .... .... .... .... .... .... .... .... .... .... X... RELAY (1 if signal is a retransmission of a received
                                                                       transmission, only some models)
    .... .... .... .... .... .... .... .... .... .... .... .X.. FLAG UNKNOWN (0 = default, but 1 is accepted and I don't
                                                                              oberserve any effects)
    .... .... .... .... .... .... .... .... .... .... .... ..X. LOWBAT (1 if battery is low, receiver gives low battery
                                                                        alert)
    .... .... .... .... .... .... .... .... .... .... .... ...X PARITY (LSB of count of set bits in previous 47 bits)
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPWMDecoder
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


class HoneywellWDB(OOKPWMDecoder):
    """Honeywell ActivLink wireless doorbell / PIR / contact (OOK_PULSE_PWM).

    175/340 µs, 48 bits, even-parity check on bit 47.
    """

    name      = "Honeywell-WDB"
    short_us  = 175.0
    long_us   = 340.0
    reset_us  = 5000.0
    n_bits    = 48
    tolerance = 0.45

    _TYPES  = {1: "PIR", 2: "Doorbell", 5: "Contact"}
    _ALERTS = {0: "Normal", 1: "High", 2: "High", 3: "Full"}

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 48:
            return None
        data = bytes(bits_to_int(bits[i : i + 8]) for i in range(0, 48, 8))
        if all(b == 0 for b in data) or all(b == 0xFF for b in data):
            return None
        # Even parity: bit 47 = parity of bits 0-46
        if sum(bits[:47]) % 2 != bits[47]:
            return None
        device_id   = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        device_type = data[2] & 0x07
        alert       = data[4] & 0x03
        open_       = (data[5] >> 6) & 0x01
        tamper      = (data[5] >> 5) & 0x01
        secret_knock= (data[5] >> 4) & 0x01
        battery_ok  = not bool((data[5] >> 1) & 0x01)
        relay       = (data[5] >> 3) & 0x01
        return DecodedPacket.from_fields(self.name, freq_hz, {
            "id":           device_id,
            "subtype":      self._TYPES.get(device_type, f"unknown({device_type})"),
            "alert":        self._ALERTS.get(alert, "High"),
            "open":         open_,
            "tampered":     tamper,
            "secret_knock": secret_knock,
            "battery_ok":   int(battery_ok),
            "relay":        relay,
            "mic":          "PARITY",
        })


__all__ = ["HoneywellWDB"]
