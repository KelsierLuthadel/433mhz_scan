"""Interlogix/GE/UTC Wireless Device Decoder.

Copyright (C) 2017 Brent Bailey <bailey.brent@gmail.com>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

Interlogix/GE/UTC Wireless Device Decoder.

Also tested with ELK-319DWM module as well as a Alula RE101 319.5MHz sensor (both short preamble).

- Frequency: 319.5 MHz

Decoding done per us patent #5761206
https://www.google.com/patents/US5761206

Protocol Bits

- 00-02 976 uS RF front porch pulse
- 03-14 12 sync pulses, logical zeros
- 15 start pulse, logical one
- 16-35 20 bit sensor identification code (ID bits 0-19)
- 36-39 4 bit device type code (DT bits 0-3)
- 40-42 3 bit trigger count (TC bit 0-2)
- 43 low battery bit
- 44 F1 latch bit NOTE that F1 latch bit and debounce are reversed.  Typo or endianness issue?
- 45 F1 debounced level
- 46 F2 latch bit
- 47 F2 debounced level
- 48 F3 latch bit (cover latch for contact sensors)
- 49 F3 debounced level
- 50 F4 latch bit
- 51 F4 debounced level
- 52 F5 positive latch bit
- 53 F5 debounced level
- 54 F5 negative latch bit
- 55 even parity over odd bits 15-55
- 56 odd parity over even bits 16-56
- 57 zero/one, programmable
- 58 RF on for 366 uS (old stop bit)
- 59 one
- 60-62 modulus 8 count of number of ones in bits 15-54
- 63 zero (new stop bit)

Protocol Description

- Bits 00 to 02 are a 976 ms RF front porch pulse, providing a wake up period that allows the
  system controller receiver to synchronize with the incoming packet.
- Bits 3 to 14 include 12 sync pulses, e.g., logical 0's, to synchronize the receiver.
- Bit 15 is a start pulse, e.g., a logical 1, that tells the receiver that data is to follow.
- Bits 16-58 provide information regarding the transmitter and associated sensor. In other
  embodiments, bits 16-58 may be replaced by an analog signal.
- Bits 16 to 35 provide a 20-bit sensor identification code that uniquely identifies the particular
  sensor sending the message. Bits 36 to 39 provide a 4 bit device-type code that identifies the
  specific-type of sensor, e.g., smoke, PIR, door, window, etc. The combination of the sensor
  bits and device bits provide a set of data bits.
- Bits 40 through 42 provide a 3-bit trigger count that is incremented for each group of message
  packets. The trigger count is a simple but effective way for preventing a third party from
  recording a message packet transmission and then re-transmitting that message packet
  transmission to make the system controller think that a valid message packet is being transmitted.
- Bit 43 provides the low battery bit.
- Bits 44 through 53 provide the latch bit value and the debounced value for each of the five inputs
  associated with the transmitter. For the F5 input, both a positive and negative latch bit are provided.
- Bit 55 provides even parity over odd bits 15 to 55.
- Bit 56 provides odd parity over even bits 16 to 56.
- Bit 57 is a programmable bit that can be used for a variety of applications, including providing an
  additional bit that could be used for the sensor identification code or device type code.
- Bit 58 is a 366 ms RF on signal that functions as the "old" stop bit. This bit provides compatibility with
  prior system controllers that may be programmed to receive a 58-bit message.
- Bit 59 is a logical 1.
- Bits 60 to 62 are a modulus eight count of the number of 1 bits in bits 15 through 54, providing enhanced
  error detection information to be used by the system controller. Finally, bit 63 is the "new" stop bit,
  e.g., a logical 0, that tells the system controller that it is the end of the message packet.

Addendum

GE/Interlogix keyfobs do not follow the documented iti protocol and it
appears the protocol was misread by the team that created the keyfobs.
The button states are sent in the three trigger count bits (bit 40-42)
and no battery status appears to be provided. 4 buttons and a single
multi-button press (buttons 1 - lock and buttons 2 - unlock) for a total
of 5 buttons available on the keyfob.

For contact sensors, latch 3 (typically the tamper/case open latch) will
float (giving misreads) if the external contacts are used (ie; closed)
and there is no 4.7 Kohm end of line resistor in place on the external
circuit.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from ..base import OOKPPMDecoder
from .._helpers import _reverse8
from ...dsp import bits_to_int
from ...packet import DecodedPacket
if TYPE_CHECKING:
    from ...dsp import Pulse


_INTERLOGIX_TYPES: dict[int, str] = {
    0xA: "contact", 0xF: "keyfob", 0x4: "motion", 0x6: "heat",
    0x9: "glass",   0xD: "glass",  0xE: "freeze", 0x2: "smoke",
    0x3: "panic",
}


class InterlogixSecurity(OOKPPMDecoder):
    """Interlogix / GE / UTC wireless security sensor (OOK_PULSE_PPM, 319.5 MHz).

    122/244 µs, 8-bit preamble (0x01) + 46 data bits, 2-bit Hamming parity.
    """

    name      = "Interlogix-Security"
    short_us  = 122.0
    long_us   = 244.0
    reset_us  = 500.0
    n_bits    = 54   # 8 preamble + 46 data
    tolerance = 0.45

    def _parse(self, bits: list[int], freq_hz: float) -> DecodedPacket | None:
        if len(bits) < 54:
            return None
        # Locate preamble 0x01 = [0,0,0,0,0,0,0,1]
        preamble = [0, 0, 0, 0, 0, 0, 0, 1]
        start = -1
        for i in range(min(16, len(bits) - 46)):
            if bits[i : i + 8] == preamble:
                start = i + 8
                break
        if start < 0 or start + 46 > len(bits):
            return None
        mb = bits[start : start + 46]
        # Pack into 6 bytes (pad 2 trailing zeros)
        msg = []
        for i in range(6):
            chunk = mb[i * 8 : i * 8 + 8]
            chunk += [0] * (8 - len(chunk))
            msg.append(bits_to_int(chunk))
        # Sanity
        if (msg[0] | msg[1] | msg[2]) == 0 or (msg[0] & msg[1] & msg[2]) == 0xFF:
            return None
        # Parity
        par = msg[0] ^ msg[1] ^ msg[2] ^ msg[3] ^ msg[4]
        par = (par >> 4) ^ (par & 0xF)
        par = (par >> 2) ^ (par & 0x3)
        par ^= msg[5] >> 6
        if (par ^ 0x3) != 0:
            return None
        serial = (_reverse8(msg[0]) << 16) | (_reverse8(msg[1]) << 8) | _reverse8(msg[2])
        dtype  = (_reverse8(msg[2]) >> 4) & 0xF
        subtype = _INTERLOGIX_TYPES.get(dtype)
        if subtype is None:
            return None
        fields: dict = {"id": f"{serial:06X}", "subtype": subtype, "mic": "PARITY"}
        if subtype == "keyfob":
            btn_code = msg[3] & 0x0E
            btn_map  = {0x4: "lock", 0x8: "unlock", 0xC: "button3",
                        0x2: "button4", 0xA: "lock+unlock"}
            fields["button"] = btn_map.get(btn_code, "unknown")
        else:
            fields["battery_ok"] = int(not bool(mb[27] if len(mb) > 27 else 0))
            for fi in range(5):
                idx = 28 + fi * 2
                fields[f"switch{fi+1}"] = "OPEN" if (idx < len(mb) and mb[idx]) else "CLOSED"
        return DecodedPacket.from_fields(self.name, freq_hz, fields)


__all__ = ["InterlogixSecurity"]
