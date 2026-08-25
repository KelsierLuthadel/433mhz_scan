"""Console display for decoded packets."""

from datetime import datetime

from .packet import DecodedPacket

# ANSI colour helpers (fallback gracefully if terminal doesn't support them)
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
DIM = "\033[2m"


def _colour(text: str, code: str) -> str:
    return f"{code}{text}{RESET}"


def format_packet(pkt: DecodedPacket, use_colour: bool = True) -> str:
    c = (lambda t, code: _colour(t, code)) if use_colour else (lambda t, _: t)

    ts = pkt.time.strftime("%H:%M:%S.%f")[:-3]
    header = (
        f"{c(ts, DIM)}  "
        f"{c(pkt.model, BOLD + GREEN)}  "
        f"[{c(pkt.freq_mhz, CYAN)}]"
    )

    # Signal quality
    rssi = pkt.raw.get("rssi")
    snr = pkt.raw.get("snr")
    sig_parts = []
    if rssi is not None:
        sig_parts.append(f"RSSI {rssi:.1f} dBm")
    if snr is not None:
        sig_parts.append(f"SNR {snr:.1f} dB")
    signal_str = c("  " + "  ".join(sig_parts), DIM) if sig_parts else ""

    # Device identity
    id_parts = []
    for key in ("id", "channel", "subtype"):
        val = pkt.raw.get(key)
        if val is not None:
            id_parts.append(f"{key}={val}")
    id_str = c("  " + " ".join(id_parts), YELLOW) if id_parts else ""

    # Payload fields
    fields = pkt.summary_fields()
    payload_parts = [f"{c(k, MAGENTA)}={v}" for k, v in fields.items()]
    payload_str = "  " + "  ".join(payload_parts) if payload_parts else ""

    return header + signal_str + id_str + payload_str


def print_packet(pkt: DecodedPacket, use_colour: bool = True) -> None:
    print(format_packet(pkt, use_colour=use_colour))


def print_startup_banner(freq_labels: list[str], mode: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  RTL-SDR Self-Contained Decoder")
    print(f"  Mode    : {mode}")
    print(f"  Freqs   : {', '.join(freq_labels)}")
    print(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")
