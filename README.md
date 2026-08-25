# SDR 433  Self-Contained RTL-SDR Packet Decoder

Listens on 433.92 MHz (ISM band) and 978 MHz (UAT ADS-B) using one or two RTL-SDR dongles and decodes packets entirely in Python. No external binaries required.

## Requirements

| Dependency | Purpose | Install |
|---|---|---|
| RTL-SDR dongle (RTL2832U-based) | Hardware |  |
| librtlsdr | Low-level SDR driver | See below |
| Python 3.12+ | Runtime | python.org |
| pyrtlsdr | RTL-SDR hardware interface | `pip install pyrtlsdr` |
| numpy | Signal processing | `pip install numpy` |
| flask | Web dashboard (`--web`) | `pip install flask` |
| paho-mqtt | MQTT output (`--mqtt-host`) | `pip install paho-mqtt` |
| pyserial | USB GPS receiver (`--gps`) | `pip install pyserial` |

**librtlsdr system dependency:**
- **Windows**  download `rtlsdr.dll` from the osmocom RTL-SDR releases page and place it on your `PATH` (or alongside `python.exe`)
- **Linux**  `sudo apt install librtlsdr-dev`
- **macOS**  `brew install librtlsdr`

Install Python packages:
```
pip install -r requirements.txt
```

## Quick start

```
python main.py
```

Listens on 433.92 MHz using RTL-SDR device 0 and prints decoded packets to the terminal.

## Options

```
python main.py --help

Device / frequency:
  --freq MHZ            Centre frequency in MHz (default: 433.92)
  -d / --device IDX     RTL-SDR device index (default: 0)
  --device-spec IDX:MHZ Device+frequency pair, e.g. 0:433.92 (repeatable)
  --dual                Two-dongle shortcut: device 0=433.92, device 1=978 MHz
  -g / --gain DB        Tuner gain in dB (0=auto, default: 40)
  --list-devices        List connected RTL-SDR devices and exit

Display:
  --no-colour           Plain text output
  --filter-model STR    Only show packets whose model contains STR

Output sinks:
  --log FILE            Append decoded packets as JSON lines to FILE
  --mqtt-host HOST      MQTT broker host (enables MQTT publishing)
  --mqtt-port PORT      MQTT broker port (default: 1883)
  --mqtt-user USER      MQTT username
  --mqtt-password PASS  MQTT password
  --mqtt-topic PREFIX   MQTT topic prefix (default: rtl_433)
  --web                 Start live web dashboard
  --web-port PORT       Web dashboard port (default: 8080)
  --web-host HOST       Web dashboard host (default: 0.0.0.0)

GPS:
  --gps PORT            Serial port of a USB GPS receiver (e.g. COM3 or /dev/ttyUSB0)
                        Attaches lat/lon/alt to every decoded packet
  --gps-baud BAUD       GPS baud rate (default: 9600)

Misc:
  -v / --verbose        Debug logging
```

## Examples

```bash
# Single dongle on 433.92 MHz
python main.py

# Two dongles simultaneously
python main.py --dual

# Explicit multi-device
python main.py --device-spec 0:433.92 --device-spec 1:978

# Log everything to a file
python main.py --log packets.jsonl

# Filter to a specific device type
python main.py --filter-model Acurite

# Web dashboard
python main.py --web

# MQTT
python main.py --mqtt-host localhost --mqtt-topic home/433

# GPS tagging (USB GPS on COM3)
python main.py --gps COM3

# All outputs combined
python main.py --dual --web --mqtt-host localhost --log packets.jsonl --gps COM3
```

## GPS tagging

When `--gps PORT` is specified, a background thread reads NMEA 0183 sentences from the GPS receiver. Every decoded packet is stamped with the current fix before being written to any output:

```json
{
  "time": "2026-08-24T14:30:00.123",
  "model": "Acurite-Tower",
  "freq": 433920000.0,
  "temperature_C": 21.5,
  "humidity": 58,
  "lat": 51.509865,
  "lon": -0.118092,
  "alt_m": 12.3,
  "gps_satellites": 7
}
```

Compatible with any USB GPS dongle that outputs standard NMEA sentences (GPRMC / GPGGA / GNRMC / GNGGA).

## Project structure

```
sdr_433/
├── main.py                          # CLI entry point
├── requirements.txt
└── sdr_receiver/
    ├── receiver.py                  # OOKReceiver + UATReceiver pipelines
    ├── dsp.py                       # I/Q → pulses → bits (OOK + FSK)
    ├── hardware.py                  # pyrtlsdr device wrapper
    ├── packet.py                    # DecodedPacket data model
    ├── gps.py                       # NMEA GPS reader (serial)
    ├── display.py                   # Coloured terminal output
    ├── logger_output.py             # JSONL file logging
    ├── mqtt_publisher.py            # MQTT publishing
    ├── runner.py                    # Multi-device threading
    ├── web_dashboard.py             # Flask live dashboard
    └── devices/
        ├── __init__.py              # DEVICE_REGISTRY (~350 decoders)
        ├── base.py                  # Abstract decoder base classes
        ├── uat978.py                # 978 MHz UAT ADS-B decoder
        ├── security/                # 22 decoders
        ├── smart_home/              # 37 decoders
        ├── weather/                 # 132 decoders
        ├── tpms/                    # 39 decoders
        ├── car_remotes/             # 12 decoders
        ├── power_energy/            # 17 decoders
        ├── water_meters/            # 18 decoders
        ├── bbq_pool_rain/           # 18 decoders
        ├── misc/                    # 42 decoders
        └── missing/                 # 12 decoders
```

## Supported devices

~350 device decoders across 10 categories. Each decoder is a single Python file in its category folder.

### Security & Alarms (22)
| Device | Protocol |
|---|---|
| Caviuse Wireless Sensor | OOK/PWM |
| Chuango Security System | OOK/PPM |
| DSC Security System | OOK/PCM |
| Generic Motion Detector | OOK/PPM |
| HCS200 / HCS361 / HCS362 | OOK/Manchester |
| Honeywell CM921 Thermostat | OOK/Manchester |
| Honeywell Security (5800 series) | OOK/PPM |
| Honeywell ActivLink WDB | OOK/PPM |
| Interlogix Security | OOK/PPM |
| Kerui Door/Motion Sensor | OOK/PWM |
| Kidde Smoke Alarm | OOK/PCM |
| RISCO Agility | OOK/PWM |
| Secplus v1 / v2 (garage door) | OOK/PPM |
| SimpliSafe (gen 1–2) | OOK/PPM |
| SimpliSafe Gen3 | OOK/Manchester |
| Smoke GS558 | OOK/PPM |
| Visonic Powercode | OOK/Manchester |
| Vivint Door/Motion Sensor | OOK/PWM |
| Yale HSA (Home Security Alarm) | Raw |

### Smart Home (37)
| Device | Notes |
|---|---|
| Blyss DC5 | Rolling-code lighting |
| Brennenstuhl RCS 2044 | Mains socket remote |
| Cardin (gate/garage) | |
| Danfoss CF-RS10 thermostat | |
| Delta Dore X3D | |
| Dickert MAHS | |
| Eberle Instat 868-R1 | |
| Elero (blind/shutter) | |
| EnOcean ERP1 | |
| FS20 | |
| Florab Best | |
| Funkbus | |
| GE Color Effects LED | |
| InnoValley KW9015B | |
| Intertechno | |
| JASCO | |
| LightwaveRF | |
| MC Power Kinetic | |
| Markisol | |
| new-KAKU (AB400D / CDB30) | |
| Nexa | |
| NiceFloR'S (gate/barrier) | |
| Norgo NGF-099 | |
| Quhwa doorbell | |
| Regency Fan | |
| RojaFlex shutter | |
| Silvercrest remote | |
| Somfy IOHC | |
| Somfy RTS | |
| Universal Fan Controller | |
| Vaillant VRT340f | |
| Watts Thermostat | |
| Watts Vision | |
| Watts WFHT-RF | |
| Waveman | |
| X10 RF / X10 Security | |

### Weather Stations (132)

#### Acurite (9)
00275RM, 01185M, 590TX, 606, 609 (legacy), 985, 986, Rain896, TH series, TXR

#### Bresser (8)
3-CH, 5-in-1, 6-in-1, 7-in-1, Garden, Leakage, Lightning, ST1005H

#### Fine Offset (12)
WH1050, WH1080, WH2 (legacy), WH31L, WH43, WH45, WH46, WH52, WH55, WN34, WS80, WS85, WS90

#### Govee / Ambient Weather (9)
H5054, H5054v2, H5059, H5112, H5310, Ambient F007TH, TX8300, WH31E, Ecowitt

#### Hideki / TFA (9)
Arexx ML, Atech WS308, Baldr Therm, Emos E6016, FT004B, Hideki TS04, KlimaLogg, Vevor 7-in-1, WEC2103

#### Nexus / Cotech family (18)
Nexus TH, Rubicson 48659, Prologue, Proove, Kedsum, S3318P, TTX201, Calibeurs RF104, GT-WT02/03, Mebus, Eurochron, Cotech 36-7900, Cotech 36-7959, Cotech FT0203, Digitech XC0324, Solight TE44

#### LaCrosse (13)
Breeze Pro, R1, TH3, TX, TX141x, TX22UIT, TX31U, TX34, TX35, WR1, WS2310, WS6868, WS7000

#### Oregon Scientific (4)
V1 (legacy), Classic, SL109H, WMR500

#### TFA Dostmann (9)
14-1504-V2, 30-3196, 30-3221, 30-3307, 30-390X, Drop 30.3233, Marbella, Pool Thermometer, TwinPlus 30-3049

#### ThermoPro (10)
TP11, TP12, TP211B, TP28b, TP828b, TP829b, TP86xb, TX2, TX2C, TX7B

#### Auriol / Alecto / InFactory group (28)
Alecto V1, Auriol 4-LD5661, AFT77B2, AFW2A1, AHFL, HG02832, HG04641A, Geevon TX16/TX19, Holman WS5029 PCM/PWM, InFactory, Inkbird ITH-20R, WT450, EFTH800, EmaxW6, Esperanza EWS, Generic Temp Sensor, Netatmo THW, Oria WA150KM, Sainlogic SA8, Sharp SPC775, Shenzhen Wale WLTH6R, Springfield Soil Moisture, Vauno EN8822C, WT0124 Pool, WS2032, WSSensor

### TPMS  Tyre Pressure Monitoring (39)

#### European (16)
Schrader, Schrader EG53MA4, Schrader MRXBC5A4, Schrader NIS315G3, Schrader SMD3MA4, Abarth 124, BMW, BMW G3, Citroën, Hyundai VDO, Mercedes-Benz, Porsche, Renault, Renault 0435R, Sefis M3, TRW

#### North American (11)
Ford (FSK), GM aftermarket, Jeep/Citroën (FSK), Honda TRW (FSK), Toyota (FSK), Nissan (FSK), Kia (FSK), Hyundai Elantra 2012 (FSK), SmarTire (Aston Martin DB9), Solar Truck (FSK), Steelmate, TyreGuard 400

#### Generic / aftermarket (12)
Airpuxem, AVE, EEzRV, GearHive, IMARS T240, Jansite, Jansite Solar, Jansite TY468, Jansite TY588, PMV107J, Schrader Motorcycle, generic Jeep/Citroën

> Note: FSK-based sensors (Ford, Honda, Toyota, Nissan, Kia, Jeep) require an FSK demodulation front-end not yet integrated into the OOK pipeline and currently return no data.

### Car Remotes (12)
Astrostart, Audiovox Pro OE3B, Chrysler, Code Alarm, Continental, Compustar 1WG3R, Ford, GM, Honda, Mic6SC2, Nidec, Opel Mokka

### Power & Energy Monitoring (17)
Blueline Power Cost Monitor, Burnhard BBQ (temperature probe), CurrentCost, EC3k, EcoEye, Efergy E2 Classic, Efergy Optical, Elster Electricity Meter, EmonTX, ESIC EMT7110, Gasmate BA1008, GEO minim+, IKEA Sparsnäs, Marlec Solar, RFXMeter, Revolt NC5462, Revolt ZX7717

### Water & Utility Meters (18)
Apator Metra EITN30 / ERM30, Arad MS Meter, Badger Orion Endpoint, Badger Water Meter, ERT IDM, ERT SCM, Flowis, Gridstream, M-Bus, Neptune R900, OilSmart / OilStandard / OilWatchman / OilWatchman Advanced, ScmPlus, SilverSpring Mesh, Watchman Plus

### BBQ / Pool / Rain (18)
Baldr HCS528ARF, Baldr Rain Gauge, Biltema Rain Gauge, Emos E6016 Rain, Grill Thermometer, Maverick ET73 / ET73x, Maverick XR30 / XR50, Quigg BBQ, RainPoint HCS012ARF, RainPoint Soil, Rubicson Pool 48942, Schou 72543 Rain, SR-Smith Pool, TFA Pool Thermometer, TSFT002, Typhur Sync Gold

### Miscellaneous (54)
ABMT, Akhan 100F14, Alps FWB1U545, ANT+, Archos TBH, Arad MS Meter, BM5, BT Rain, Calex EA220 (CED7000), Celsia CZC1, Chamberlain CWPIRC, CMR113, Companion WTR001, CTT Life Power Hybrid, DirecTV, Dish Remote 63, Ecodhome, Elro DB286A, Elsner Solexa, ELV EM1000, ELV WS2000, EN2058, ESA1000, ESun EN2053, FSL Scoreboard, Generic Remote, GT-TMBBQ05, Hanwell ML4000, Homelead HG9901, HT680, IBIS Beacon, Insteon, Martec MPLCD, Megacode, Missil ML0757, Mueller Hotrod, Omni Multisensor, Opus XT300, Philips AJ3650 / AJ7010, Proflame 2, Quinetic, RadioHead ASK, RF-Tech, RFM69/Moteino, Rosstech DCU-706, Siemens 5WY72xx, Telldus FT0385R, Thermor DG950, Thermor A6N132TX, TR502MSV, 2GIG Key2e, WallarGe CLTX001, WgPb12v1

### UAT ADS-B  978 MHz
978 MHz Universal Access Transceiver (UAT) aircraft position reports. Decoded fields include ICAO address, callsign, altitude, latitude, longitude, ground speed, and track.

## Decoder architecture

Each device is implemented as a single Python class in its category subfolder (`devices/security/YaleHSA.py`, etc.). Decoders inherit from one of six base classes:

| Base class | Modulation |
|---|---|
| `OOKPWMDecoder` | OOK Pulse Width Modulation |
| `OOKPPMDecoder` | OOK Pulse Position Modulation |
| `OOKPCMDecoder` | OOK Pulse Code Modulation / NRZ |
| `ManchesterDecoder` | OOK Manchester / NRZS |
| `FSKPCMDecoder` | FSK CPFSK demodulation |
| `RawDecoder` | Complex / multi-mode protocols |

The `DEVICE_REGISTRY` in `devices/__init__.py` is a flat list of decoder instances. Each decoded packet is tried against every registered decoder in order; the first match wins. Unrecognised packets are silently discarded.

## Output format

Every matched packet is emitted as a JSON object. Example:

```json
{
  "time": "2026-08-24T14:30:00.123",
  "model": "Acurite-Tower",
  "freq": 433920000.0,
  "id": "0x1a2b",
  "channel": 1,
  "temperature_C": 21.5,
  "humidity": 58,
  "battery_ok": true,
  "lat": 51.509865,
  "lon": -0.118092,
  "alt_m": 12.3
}
```

Fields depend on the device type. Location fields (`lat`, `lon`, `alt_m`) are present only when `--gps` is active and a GPS fix is available.
