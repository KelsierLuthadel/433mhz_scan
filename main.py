#!/usr/bin/env python3
"""RTL-SDR self-contained packet decoder  433.92 MHz & 978 MHz.

Self-contained: talks directly to the RTL-SDR hardware via pyrtlsdr.
No external rtl_433 binary required.

Usage examples:
    python main.py                              # device 0 on 433.92 MHz
    python main.py --freq 978                   # device 0 on 978 MHz (UAT)
    python main.py --dual                       # device 0=433.92  device 1=978
    python main.py --device-spec 0:433.92       # explicit device+freq
    python main.py --device-spec 0:433.92 --device-spec 1:978
    python main.py --web                        # open http://localhost:8080
    python main.py --mqtt-host localhost        # publish to MQTT broker
    python main.py --log packets.jsonl          # append JSONL file
    python main.py --list-devices               # list connected dongles
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading

from sdr_receiver.display import print_packet, print_startup_banner
from sdr_receiver.hardware import list_devices
from sdr_receiver.logger_output import JsonlLogger
from sdr_receiver.packet import DecodedPacket
from sdr_receiver.receiver import OOKReceiver, UATReceiver, UAT_FREQ_HZ
from sdr_receiver.runner import (
    DEFAULT_DUAL,
    DeviceSpec,
    drain,
    parse_device_specs,
    start_multi_receiver,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Self-contained RTL-SDR packet decoder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # -- Device / frequency --
    p.add_argument("--freq", type=float, default=433.92, metavar="MHZ",
                   help="Centre frequency in MHz (default: 433.92)")
    p.add_argument("-d", "--device", type=int, default=0, metavar="IDX",
                   help="RTL-SDR device index (default: 0)")
    p.add_argument("--device-spec", dest="device_specs", action="append", metavar="IDX:MHZ",
                   help="Device+frequency pair, e.g. 0:433.92  (repeatable)")
    p.add_argument("--dual", action="store_true",
                   help="Two-dongle shortcut: device 0=433.92 MHz, device 1=978 MHz")
    p.add_argument("-g", "--gain", type=float, default=40.0, metavar="DB",
                   help="Tuner gain in dB (0 = auto, default: 40)")
    p.add_argument("--list-devices", action="store_true",
                   help="Print connected RTL-SDR devices and exit")

    # -- Display --
    p.add_argument("--no-colour", action="store_true", help="Disable ANSI colour")
    p.add_argument("--filter-model", metavar="STR",
                   help="Only show packets whose model contains STR (case-insensitive)")

    # -- Outputs --
    p.add_argument("--log", metavar="FILE", help="Append decoded packets as JSON lines to FILE")

    # -- MQTT --
    p.add_argument("--mqtt-host", metavar="HOST", help="MQTT broker host (enables MQTT output)")
    p.add_argument("--mqtt-port", type=int, default=1883, metavar="PORT")
    p.add_argument("--mqtt-user", metavar="USER")
    p.add_argument("--mqtt-password", metavar="PASS")
    p.add_argument("--mqtt-topic", default="rtl_433", metavar="PREFIX",
                   help="MQTT topic prefix (default: rtl_433)")

    # -- Web dashboard --
    p.add_argument("--web", action="store_true", help="Start live web dashboard")
    p.add_argument("--web-port", type=int, default=8080, metavar="PORT")
    p.add_argument("--web-host", default="0.0.0.0", metavar="HOST")

    # -- GPS --
    p.add_argument("--gps", metavar="PORT",
                   help="Serial port of a USB GPS receiver (e.g. COM3 or /dev/ttyUSB0). "
                        "Attaches lat/lon to every decoded packet.")
    p.add_argument("--gps-baud", type=int, default=9600, metavar="BAUD",
                   help="GPS serial baud rate (default: 9600)")

    # -- Misc --
    p.add_argument("-v", "--verbose", action="store_true", help="Debug logging")

    return p.parse_args()


def _dispatch(
    pkt: DecodedPacket,
    *,
    use_colour: bool,
    model_filter: str | None,
    file_logger,
    mqtt,
    dashboard,
    gps_reader=None,
) -> None:
    if gps_reader is not None:
        pkt.stamp_location(gps_reader.fix)
    if model_filter and model_filter not in pkt.model.lower():
        return
    print_packet(pkt, use_colour=use_colour)
    if file_logger:
        file_logger.log(pkt)
    if mqtt:
        mqtt.publish(pkt)
    if dashboard:
        dashboard.state.push(pkt)


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if args.list_devices:
        devices = list_devices()
        if not devices:
            print("No RTL-SDR devices found (or pyrtlsdr not installed).")
        for d in devices:
            print(f"  [{d['index']}] {d['name']}")
        return

    # ── Build device spec list ──────────────────────────────────────────
    if args.dual:
        specs = DEFAULT_DUAL
        mode  = "dual-dongle (device 0=433.92 MHz, device 1=978 MHz)"
    elif args.device_specs:
        specs = parse_device_specs(args.device_specs)
        mode  = "multi-device"
    else:
        # Single device / single frequency
        specs = [DeviceSpec(device_index=args.device, freq_hz=args.freq * 1e6, gain=args.gain)]
        mode  = "single"

    for spec in specs:
        spec.gain = args.gain

    freq_labels = [f"{s.freq_hz/1e6:.3f} MHz (dev#{s.device_index})" for s in specs]
    print_startup_banner(freq_labels, mode)

    # ── Optional sinks ──────────────────────────────────────────────────
    mqtt = None
    if args.mqtt_host:
        from sdr_receiver.mqtt_publisher import MqttConfig, MqttPublisher
        cfg  = MqttConfig(
            host=args.mqtt_host, port=args.mqtt_port,
            username=args.mqtt_user, password=args.mqtt_password,
            topic_prefix=args.mqtt_topic,
        )
        mqtt = MqttPublisher(cfg)
        mqtt.connect()
        print(f"  MQTT      : {args.mqtt_host}:{args.mqtt_port}/{args.mqtt_topic}/#")

    dashboard = None
    if args.web:
        from sdr_receiver.web_dashboard import Dashboard, DashboardState
        state     = DashboardState()
        dashboard = Dashboard(state, host=args.web_host, port=args.web_port)
        dashboard.start()

    file_logger = JsonlLogger(args.log) if args.log else None

    gps_reader = None
    if args.gps:
        from sdr_receiver.gps import GPSReader
        gps_reader = GPSReader(args.gps, baud=args.gps_baud)
        gps_reader.start()
        print(f"  GPS       : {args.gps} @ {args.gps_baud} baud")

    dispatch_kw = dict(
        use_colour=not args.no_colour,
        model_filter=args.filter_model.lower() if args.filter_model else None,
        file_logger=file_logger,
        mqtt=mqtt,
        dashboard=dashboard,
        gps_reader=gps_reader,
    )

    # ── Interrupt handling ──────────────────────────────────────────────
    stop_event = threading.Event()

    def _sigint(sig, frame):
        stop_event.set()
        print("\n[Interrupted]")
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _sigint)

    # ── Main packet loop ────────────────────────────────────────────────
    try:
        if len(specs) == 1 and mode == "single":
            # Single-device path  no threads needed
            spec = specs[0]
            is_uat = abs(spec.freq_hz - UAT_FREQ_HZ) < 10e6
            rx = UATReceiver(device_index=spec.device_index, gain=spec.gain) if is_uat \
                 else OOKReceiver(device_index=spec.device_index, freq_hz=spec.freq_hz, gain=spec.gain)
            for pkt in rx.stream():
                if stop_event.is_set():
                    break
                _dispatch(pkt, **dispatch_kw)
        else:
            # Multi-device path  one thread per dongle
            q, thread_stop = start_multi_receiver(specs)
            for pkt in drain(q, thread_stop):
                if stop_event.is_set():
                    thread_stop.set()
                    break
                _dispatch(pkt, **dispatch_kw)

    except KeyboardInterrupt:
        pass
    except RuntimeError as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        if file_logger:
            file_logger.close()
        if mqtt:
            mqtt.close()
        if gps_reader:
            gps_reader.stop()


if __name__ == "__main__":
    main()
