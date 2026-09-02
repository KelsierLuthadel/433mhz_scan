"""Console display for decoded packets  rtl_433 kv-format output."""

from datetime import datetime

from .packet import DecodedPacket

RESET   = "\033[0m"
BOLD    = "\033[1m"
CYAN    = "\033[36m"
YELLOW  = "\033[33m"
WHITE   = "\033[97m"
DIM     = "\033[2m"

_UNITS = {
    "temperature_C":  " °C",
    "temperature_1_C": " °C",
    "temperature_2_C": " °C",
    "humidity":       " %",
    "pressure_hPa":   " hPa",
    "wind_speed_ms":  " m/s",
    "wind_dir_deg":   " °",
    "rain_mm":        " mm",
    "rain_rate_mm_h": " mm/h",
    "distance_mm":    " mm",
}


def _fmt_value(key: str, value) -> str:
    unit = _UNITS.get(key, "")
    if isinstance(value, float):
        formatted = f"{value:.2f}".rstrip("0").rstrip(".")
        return f"{formatted}{unit}"
    return f"{value}{unit}"


def format_packet(pkt: DecodedPacket, use_colour: bool = True) -> str:
    def c(text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if use_colour else text

    lines: list[str] = []

    # time and model header
    ts = pkt.time.strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"{'time':<10}: {c(ts, DIM)}")
    lines.append(f"{'model':<10}: {c(pkt.model, BOLD + WHITE)}")

    _skip = {"time", "model", "freq", "frequency"}
    for key, val in pkt.raw.items():
        if key in _skip:
            continue
        fval = _fmt_value(key, val)
        lines.append(f"{key:<10}: {c(fval, CYAN)}")

    return "\n".join(lines)


def print_packet(pkt: DecodedPacket, use_colour: bool = True) -> None:
    print(format_packet(pkt, use_colour=use_colour))
    print()


def print_startup_banner(freq_labels: list[str], mode: str) -> None:
    print(f"\n{'_' * 60}")
    print(f"  RTL-SDR Decoder")
    print(f"  Mode    : {mode}")
    print(f"  Freqs   : {', '.join(freq_labels)}")
    print(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'_' * 60}\n")
