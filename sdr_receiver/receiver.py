"""Main receiver pipelines: hardware samples → DecodedPacket.

OOKReceiver   433 MHz and other OOK/ASK ISM bands
UATReceiver   978 MHz UAT ADS-B (CPFSK)
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from collections.abc import Generator
from time import monotonic

from .devices import try_decode, try_decode_fsk
from .devices.uat978 import UATDecoder
from .dsp import RESET_GAP_US, demodulate_ook, extract_packets
from .hardware import CHUNK_SAMPLES, SDRDevice
from .packet import DecodedPacket

logger = logging.getLogger(__name__)

# UAT requires a specific sample rate tied to its bit rate
UAT_SAMPLE_RATE  = 2_083_334
UAT_FREQ_HZ      = 978e6
OOK_SAMPLE_RATE  = 250_000

_uat_decoder = UATDecoder()

# Longest real protocol (Roboguard) uses 216 pulses; anything beyond this is noise
MAX_PACKET_PULSES = 400


class _RepeatFilter:
    """Pass a packet only once it has been seen min_count times within window_s seconds.

    Real transmitters repeat the same burst 3-10 times in quick succession.
    Noise produces a different random decode each time, so it never accumulates.
    """

    def __init__(self, min_count: int = 2, window_s: float = 5.0) -> None:
        self._min = min_count
        self._window = window_s
        self._seen: dict[tuple, list[float]] = defaultdict(list)

    def allow(self, pkt: DecodedPacket) -> bool:
        key = (pkt.model, str(pkt.raw.get("id", "")))
        now = monotonic()
        times = self._seen[key]
        times.append(now)
        cutoff = now - self._window
        self._seen[key] = [t for t in times if t >= cutoff]
        return len(self._seen[key]) >= self._min


class OOKReceiver:
    """Decode OOK/ASK signals on one device+frequency."""

    def __init__(
        self,
        device_index: int = 0,
        freq_hz: float = 433.92e6,
        gain: float | str = 40.0,
        sample_rate: int = OOK_SAMPLE_RATE,
        chunk: int = CHUNK_SAMPLES,
    ) -> None:
        self.device_index = device_index
        self.freq_hz = freq_hz
        self.gain = gain
        self.sample_rate = sample_rate
        self.chunk = chunk

    def stream(
        self, stop: threading.Event | None = None
    ) -> Generator[DecodedPacket, None, None]:
        repeat = _RepeatFilter()
        with SDRDevice(
            device_index=self.device_index,
            center_freq=self.freq_hz,
            sample_rate=self.sample_rate,
            gain=self.gain,
        ) as dev:
            for samples in dev.stream(self.chunk):
                if stop and stop.is_set():
                    break
                # OOK pipeline
                pulses = demodulate_ook(samples, self.sample_rate)
                packets = extract_packets(pulses, reset_us=RESET_GAP_US)
                for packet_pulses in packets:
                    if len(packet_pulses) > MAX_PACKET_PULSES:
                        continue
                    pkt = try_decode(packet_pulses, self.freq_hz)
                    if pkt is not None and repeat.allow(pkt):
                        yield pkt

                # FSK pipeline (runs on the same raw IQ samples)
                fsk_pkt = try_decode_fsk(samples, self.sample_rate, self.freq_hz)
                if fsk_pkt is not None and repeat.allow(fsk_pkt):
                    yield fsk_pkt


class UATReceiver:
    """Decode UAT 978 MHz ADS-B signals."""

    def __init__(
        self,
        device_index: int = 0,
        gain: float | str = 40.0,
        chunk: int = CHUNK_SAMPLES,
    ) -> None:
        self.device_index = device_index
        self.gain = gain
        self.chunk = chunk

    def stream(
        self, stop: threading.Event | None = None
    ) -> Generator[DecodedPacket, None, None]:
        with SDRDevice(
            device_index=self.device_index,
            center_freq=UAT_FREQ_HZ,
            sample_rate=UAT_SAMPLE_RATE,
            gain=self.gain,
        ) as dev:
            for samples in dev.stream(self.chunk):
                if stop and stop.is_set():
                    break
                for pkt in _uat_decoder.decode_chunk(samples, UAT_SAMPLE_RATE):
                    yield pkt
