"""Multi-device concurrent receiver.

Each DeviceSpec runs in its own daemon thread, pushing DecodedPackets into
a shared queue.  The caller drains the queue in the main thread.
"""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Generator
from dataclasses import dataclass, field

from .packet import DecodedPacket
from .receiver import OOKReceiver, UATReceiver, UAT_FREQ_HZ

logger = logging.getLogger(__name__)


@dataclass
class DeviceSpec:
    device_index: int
    freq_hz: float
    gain: float | str = 40.0


# Shortcut: two dongles, each on one band
DEFAULT_DUAL: list[DeviceSpec] = [
    DeviceSpec(device_index=0, freq_hz=433.92e6),
    DeviceSpec(device_index=1, freq_hz=UAT_FREQ_HZ),
]


def parse_device_specs(spec_strs: list[str]) -> list[DeviceSpec]:
    """Parse "IDX:FREQ_MHz" strings, e.g. "0:433.92" or "1:978"."""
    specs: list[DeviceSpec] = []
    for s in spec_strs:
        idx_part, _, freq_part = s.partition(":")
        idx = int(idx_part.strip())
        freq = float(freq_part.strip()) * 1e6 if freq_part else 433.92e6
        specs.append(DeviceSpec(device_index=idx, freq_hz=freq))
    return specs


def _worker(spec: DeviceSpec, out: queue.Queue, stop: threading.Event) -> None:
    is_uat = abs(spec.freq_hz - UAT_FREQ_HZ) < 10e6
    try:
        if is_uat:
            rx = UATReceiver(device_index=spec.device_index, gain=spec.gain)
        else:
            rx = OOKReceiver(device_index=spec.device_index, freq_hz=spec.freq_hz, gain=spec.gain)

        for pkt in rx.stream(stop=stop):
            out.put(pkt)
            if stop.is_set():
                return
    except Exception as exc:
        logger.error("Device %d (%.2f MHz) crashed: %s", spec.device_index, spec.freq_hz / 1e6, exc)


def start_multi_receiver(
    specs: list[DeviceSpec],
) -> tuple[queue.Queue, threading.Event]:
    """Spawn one daemon thread per spec; return (queue, stop_event)."""
    q: queue.Queue = queue.Queue()
    stop = threading.Event()
    for spec in specs:
        t = threading.Thread(
            target=_worker,
            args=(spec, q, stop),
            name=f"sdr-dev{spec.device_index}",
            daemon=True,
        )
        t.start()
        logger.info("Started thread for device %d at %.3f MHz", spec.device_index, spec.freq_hz / 1e6)
    return q, stop


def drain(
    q: queue.Queue,
    stop: threading.Event,
    timeout: float = 0.1,
) -> Generator[DecodedPacket, None, None]:
    """Yield packets from the queue until stop is set."""
    while not stop.is_set():
        try:
            yield q.get(timeout=timeout)
        except queue.Empty:
            continue
