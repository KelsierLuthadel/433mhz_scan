"""Main receiver pipelines: hardware samples → DecodedPacket.

OOKReceiver   433 MHz and other OOK/ASK ISM bands
UATReceiver   978 MHz UAT ADS-B (CPFSK)
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Generator

from .devices import try_decode
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
        with SDRDevice(
            device_index=self.device_index,
            center_freq=self.freq_hz,
            sample_rate=self.sample_rate,
            gain=self.gain,
        ) as dev:
            for samples in dev.stream(self.chunk):
                if stop and stop.is_set():
                    break
                pulses = demodulate_ook(samples, self.sample_rate)
                if pulses:
                    widths = [round(p.pulse_us) for p in pulses[:8]]
                    logger.debug("chunk: %d pulses, widths(us)=%s", len(pulses), widths)
                packets = extract_packets(pulses, reset_us=RESET_GAP_US)
                if packets:
                    logger.debug("packets found: %d", len(packets))
                for packet_pulses in packets:
                    pkt = try_decode(packet_pulses, self.freq_hz)
                    if pkt is not None:
                        yield pkt
                    else:
                        widths = [(round(p.pulse_us), round(p.gap_us)) for p in packet_pulses[:6]]
                        logger.debug("no decoder matched (%d pulses) pulse/gap(us)=%s", len(packet_pulses), widths)


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
