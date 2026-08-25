"""Weather device decoders  one class per file, all re-exported here."""

# nexus group
from .NexusTH import NexusTH
from .Rubicson import Rubicson
from .Rubicson48659 import Rubicson48659
from .Prologue import Prologue
from .Proove import Proove
from .Kedsum import Kedsum
from .S3318P import S3318P
from .TTX201 import TTX201
from .CalibeursRF104 import CalibeursRF104
from .GtWt02 import GtWt02
from .GtWt03 import GtWt03
from .Mebus import Mebus
from .Eurochron import Eurochron
from .Cotech36_7900 import Cotech36_7900
from .Cotech36_7959 import Cotech36_7959
from .CotechFT0203 import CotechFT0203
from .DigitechXC0324 import DigitechXC0324
from .SolightTE44 import SolightTE44

# lacrosse group
from .LaCrosseTX import LaCrosseTX
from .LaCrosseTX141x import LaCrosseTX141x
from .LaCrosseWS7000 import LaCrosseWS7000
from .LaCrosseWS2310 import LaCrosseWS2310
from .LaCrosseTH3 import LaCrosseTH3
from .LaCrosseR1 import LaCrosseR1
from .LaCrosseTX22UIT import LaCrosseTX22UIT
from .LaCrosseTX31U import LaCrosseTX31U
from .LaCrosseTX34 import LaCrosseTX34
from .LaCrosseTX35 import LaCrosseTX35
from .LaCrosseWR1 import LaCrosseWR1
from .LaCrosseWS6868 import LaCrosseWS6868
from .LaCrosseBreezePro import LaCrosseBreezePro

# acurite group
from .AcuriteRain896 import AcuriteRain896
from .AcuriteTH import AcuriteTH
from .AcuriteTXR import AcuriteTXR
from .Acurite986 import Acurite986
from .Acurite985 import Acurite985
from .Acurite606 import Acurite606
from .Acurite00275RM import Acurite00275RM
from .Acurite590TX import Acurite590TX
from .Acurite01185M import Acurite01185M

# bresser group
from .bresser3ch import Bresser3CH
from .bresser5in1 import Bresser5in1
from .bresser6in1 import Bresser6in1
from .bresser7in1 import Bresser7in1
from .bressergarden import BresserGarden
from .bresserleakage import BresserLeakage
from .bresserlightning import BresserLightning
from .bresserst1005h import BresserST1005H

# fineoffset group
from .fineoffsetwh1050 import FineOffsetWH1050
from .fineoffsetwh1080 import FineOffsetWH1080
from .fineoffsetwh31l import FineOffsetWH31L
from .fineoffsetwh43 import FineOffsetWH43
from .fineoffsetwh45 import FineOffsetWH45
from .fineoffsetwh46 import FineOffsetWH46
from .fineoffsetwh52 import FineOffsetWH52
from .fineoffsetwh55 import FineOffsetWH55
from .fineoffsetwn34 import FineOffsetWN34
from .fineoffsetws80 import FineOffsetWS80
from .fineoffsetws85 import FineOffsetWS85
from .fineoffsetws90 import FineOffsetWS90

# govee group
from .GoveeH5054 import GoveeH5054
from .GoveeH5054v2 import GoveeH5054v2
from .GoveeH5059 import GoveeH5059
from .GoveeH5112 import GoveeH5112
from .GoveeH5310 import GoveeH5310
from .AmbientWeatherF007TH import AmbientWeatherF007TH
from .AmbientWeatherTX8300 import AmbientWeatherTX8300
from .AmbientWeatherWH31E import AmbientWeatherWH31E
from .Ecowitt import Ecowitt

# hideki group
from .HidekiTS04 import HidekiTS04
from .KlimaLogg import KlimaLogg
from .ArexxML import ArexxML
from .EmosE6016 import EmosE6016
from .AtechWS308 import AtechWS308
from .BaldrTherm import BaldrTherm
from .FT004B import FT004B
from .WEC2103 import WEC2103
from .Vevor7in1 import Vevor7in1

# oregon group
from .OregonScientific import OregonScientific
from .OregonScientificSL109H import OregonScientificSL109H
from .OregonScientificV1 import OregonScientificV1
from .OregonScientificWMR500 import OregonScientificWMR500

# tfa group
from .TFA14_1504_V2 import TFA14_1504_V2
from .TFA30_3196 import TFA30_3196
from .TFA30_3221 import TFA30_3221
from .TFA30_3307 import TFA30_3307
from .TFA30_390X import TFA30_390X
from .TFADrop303233 import TFADrop303233
from .TFAMarbella import TFAMarbella
from .TFAPoolThermometer import TFAPoolThermometer
from .TFATwinPlus303049 import TFATwinPlus303049

# thermopro group
from .ThermoProTP11 import ThermoProTP11
from .ThermoProTP12 import ThermoProTP12
from .ThermoProTX2 import ThermoProTX2
from .ThermoProTX2C import ThermoProTX2C
from .ThermoProTP211B import ThermoProTP211B
from .ThermoProTP28b import ThermoProTP28b
from .ThermoProTP828b import ThermoProTP828b
from .ThermoProTP829b import ThermoProTP829b
from .ThermoProTP86xb import ThermoProTP86xb
from .ThermoProTX7B import ThermoProTX7B

# auriol_a group
from .Auriol4LD5661 import Auriol4LD5661
from .AuriolAFT77B2 import AuriolAFT77B2
from .AuriolAFW2A1 import AuriolAFW2A1
from .AuriolAHFL import AuriolAHFL
from .AuriolHG02832 import AuriolHG02832
from .AuriolHG04641A import AuriolHG04641A
from .AlectoV1 import AlectoV1
from .GeevonTX16 import GeevonTX16
from .GeevonTX19 import GeevonTX19
from .HolmanWS5029PCM import HolmanWS5029PCM
from .HolmanWS5029PWM import HolmanWS5029PWM
from .InFactory import InFactory
from .InkbirdITH20R import InkbirdITH20R
from .WT450 import WT450

# auriol_b group
from .WT0124PoolThermometer import WT0124PoolThermometer
from .WSSensor import WSSensor
from .WS2032 import WS2032
from .SpringfieldSoilMoisture import SpringfieldSoilMoisture
from .EsperanzaEWS import EsperanzaEWS
from .GenericTemperatureSensor import GenericTemperatureSensor
from .NetatmoTHW import NetatmoTHW
from .SharpSPC775 import SharpSPC775
from .ShenzhenWaleWLTH6R import ShenzhenWaleWLTH6R
from .SainlogicSA8 import SainlogicSA8
from .OriaWA150KM import OriaWA150KM
from .EFTH800 import EFTH800
from .EmaxW6 import EmaxW6
from .VaunoEN8822C import VaunoEN8822C

# legacy
from .Acurite609 import Acurite609
from .FineOffsetWH2 import FineOffsetWH2
from .NexusTHLegacy import NexusTHLegacy

__all__ = [
    # nexus group
    "NexusTH",
    "Rubicson",
    "Rubicson48659",
    "Prologue",
    "Proove",
    "Kedsum",
    "S3318P",
    "TTX201",
    "CalibeursRF104",
    "GtWt02",
    "GtWt03",
    "Mebus",
    "Eurochron",
    "Cotech36_7900",
    "Cotech36_7959",
    "CotechFT0203",
    "DigitechXC0324",
    "SolightTE44",
    # lacrosse group
    "LaCrosseTX",
    "LaCrosseTX141x",
    "LaCrosseWS7000",
    "LaCrosseWS2310",
    "LaCrosseTH3",
    "LaCrosseR1",
    "LaCrosseTX22UIT",
    "LaCrosseTX31U",
    "LaCrosseTX34",
    "LaCrosseTX35",
    "LaCrosseWR1",
    "LaCrosseWS6868",
    "LaCrosseBreezePro",
    # acurite group
    "AcuriteRain896",
    "AcuriteTH",
    "AcuriteTXR",
    "Acurite986",
    "Acurite985",
    "Acurite606",
    "Acurite00275RM",
    "Acurite590TX",
    "Acurite01185M",
    # bresser group
    "Bresser3CH",
    "Bresser5in1",
    "Bresser6in1",
    "Bresser7in1",
    "BresserGarden",
    "BresserLeakage",
    "BresserLightning",
    "BresserST1005H",
    # fineoffset group
    "FineOffsetWH1050",
    "FineOffsetWH1080",
    "FineOffsetWH31L",
    "FineOffsetWH43",
    "FineOffsetWH45",
    "FineOffsetWH46",
    "FineOffsetWH52",
    "FineOffsetWH55",
    "FineOffsetWN34",
    "FineOffsetWS80",
    "FineOffsetWS85",
    "FineOffsetWS90",
    # govee group
    "GoveeH5054",
    "GoveeH5054v2",
    "GoveeH5059",
    "GoveeH5112",
    "GoveeH5310",
    "AmbientWeatherF007TH",
    "AmbientWeatherTX8300",
    "AmbientWeatherWH31E",
    "Ecowitt",
    # hideki group
    "HidekiTS04",
    "KlimaLogg",
    "ArexxML",
    "EmosE6016",
    "AtechWS308",
    "BaldrTherm",
    "FT004B",
    "WEC2103",
    "Vevor7in1",
    # oregon group
    "OregonScientific",
    "OregonScientificSL109H",
    "OregonScientificV1",
    "OregonScientificWMR500",
    # tfa group
    "TFA14_1504_V2",
    "TFA30_3196",
    "TFA30_3221",
    "TFA30_3307",
    "TFA30_390X",
    "TFADrop303233",
    "TFAMarbella",
    "TFAPoolThermometer",
    "TFATwinPlus303049",
    # thermopro group
    "ThermoProTP11",
    "ThermoProTP12",
    "ThermoProTX2",
    "ThermoProTX2C",
    "ThermoProTP211B",
    "ThermoProTP28b",
    "ThermoProTP828b",
    "ThermoProTP829b",
    "ThermoProTP86xb",
    "ThermoProTX7B",
    # auriol_a group
    "Auriol4LD5661",
    "AuriolAFT77B2",
    "AuriolAFW2A1",
    "AuriolAHFL",
    "AuriolHG02832",
    "AuriolHG04641A",
    "AlectoV1",
    "GeevonTX16",
    "GeevonTX19",
    "HolmanWS5029PCM",
    "HolmanWS5029PWM",
    "InFactory",
    "InkbirdITH20R",
    "WT450",
    # auriol_b group
    "WT0124PoolThermometer",
    "WSSensor",
    "WS2032",
    "SpringfieldSoilMoisture",
    "EsperanzaEWS",
    "GenericTemperatureSensor",
    "NetatmoTHW",
    "SharpSPC775",
    "ShenzhenWaleWLTH6R",
    "SainlogicSA8",
    "OriaWA150KM",
    "EFTH800",
    "EmaxW6",
    "VaunoEN8822C",
    # legacy
    "Acurite609",
    "FineOffsetWH2",
    "NexusTHLegacy",
]
