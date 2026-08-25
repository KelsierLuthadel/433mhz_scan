"""RTL-SDR hardware interface via pyrtlsdr."""

from __future__ import annotations

import logging
from collections.abc import Generator

import numpy as np

logger = logging.getLogger(__name__)

_RTLSDR_ERROR: str | None = None
try:
    from rtlsdr import RtlSdr as _RtlSdr  # type: ignore
    _HAS_RTLSDR = True
except ImportError:
    _HAS_RTLSDR = False
    _RTLSDR_ERROR = (
        "pyrtlsdr is not installed. Install it with:\n"
        "  pip install pyrtlsdr"
    )
except AttributeError as _e:
    # ctypes raises AttributeError when a symbol is missing from librtlsdr.so.
    # Most commonly: 'rtlsdr_set_dithering' absent on librtlsdr < 0.6 (2019).
    # The system package (apt/dnf) is usually too old; build from source instead.
    _HAS_RTLSDR = False
    _RTLSDR_ERROR = (
        f"librtlsdr is too old or incompatible ({_e}).\n"
        "pyrtlsdr requires librtlsdr 0.6+ with rtlsdr_set_dithering support.\n"
        "\n"
        "Fix on Debian/Ubuntu  build from source:\n"
        "  sudo apt remove librtlsdr-dev librtlsdr0 rtl-sdr\n"
        "  sudo apt install cmake libusb-1.0-0-dev pkg-config\n"
        "  git clone https://gitea.osmocom.org/sdr/rtl-sdr\n"
        "  cd rtl-sdr && mkdir build && cd build\n"
        "  cmake .. -DINSTALL_UDEV_RULES=ON\n"
        "  make && sudo make install && sudo ldconfig\n"
        "\n"
        "Or downgrade pyrtlsdr to avoid the dependency:\n"
        "  pip install 'pyrtlsdr==0.2.91'"
    )

CHUNK_SAMPLES = 256 * 1024


class SDRDevice:
    def __init__(
        self,
        device_index: int = 0,
        center_freq: float = 433.92e6,
        sample_rate: int = 250_000,
        gain: float | str = 40.0,
    ) -> None:
        if not _HAS_RTLSDR:
            raise RuntimeError(_RTLSDR_ERROR or "RTL-SDR is unavailable.")
        self.device_index = device_index
        self.center_freq = center_freq
        self.sample_rate = sample_rate
        self.gain = gain
        self._sdr: "_RtlSdr | None" = None

    def open(self) -> None:
        self._sdr = _RtlSdr(device_index=self.device_index)
        self._sdr.center_freq = self.center_freq
        self._sdr.sample_rate = self.sample_rate
        self._sdr.gain = "auto" if (self.gain == "auto" or self.gain == 0) else self.gain
        logger.info(
            "Device %d: %.3f MHz  %d sps  gain=%s",
            self.device_index, self.center_freq / 1e6, self.sample_rate, self.gain,
        )

    def close(self) -> None:
        if self._sdr is not None:
            try:
                self._sdr.close()
            except Exception:
                pass
            self._sdr = None

    def stream(self, chunk: int = CHUNK_SAMPLES) -> Generator[np.ndarray, None, None]:
        """Yield complex64 numpy arrays indefinitely."""
        if self._sdr is None:
            raise RuntimeError("Call open() before stream()")
        while True:
            yield np.array(self._sdr.read_samples(chunk), dtype=np.complex64)

    def __enter__(self) -> "SDRDevice":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def list_devices() -> list[dict]:
    """Return a list of connected RTL-SDR devices."""
    if not _HAS_RTLSDR:
        return []
    try:
        count = _RtlSdr.get_device_count()
        return [
            {"index": i, "name": _RtlSdr.get_device_name(i)}
            for i in range(count)
        ]
    except Exception as exc:
        logger.warning("Could not list devices: %s", exc)
        return []
