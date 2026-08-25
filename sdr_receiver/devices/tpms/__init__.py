"""tpms  TPMS device decoder package.

One file per device; sources: tpms_euro.py, tpms_usa.py, tpms_misc.py.
"""
# Euro-source classes
from .Schraeder import Schraeder
from .SchraeaderEG53MA4 import SchraeaderEG53MA4
from .SchraeaderMRXBC5A4 import SchraeaderMRXBC5A4
from .SchraeaderSMD3MA4 import SchraeaderSMD3MA4
from .SchraeaderNIS315G3 import SchraeaderNIS315G3
from .TPMSBmw import TPMSBmw
from .TPMSBmwG3 import TPMSBmwG3
from .TPMSCitroen import TPMSCitroen
from .TPMSMercedesBenz import TPMSMercedesBenz
from .TPMSRenault import TPMSRenault
from .TPMSRenault0435R import TPMSRenault0435R
from .TPMSPorsche import TPMSPorsche
from .TPMSTRW import TPMSTRW
from .TPMSHyundaiVDO import TPMSHyundaiVDO
from .TPMSSefisM3 import TPMSSefisM3
from .TPMSAbarth124 import TPMSAbarth124

# USA-source classes
from .Steelmate import Steelmate
from .TpmsElantra2012 import TpmsElantra2012
from .TpmsFord import TpmsFord
from .TpmsGm import TpmsGm
from .TpmsHonda import TpmsHonda
from .TpmsKia import TpmsKia
from .TpmsNissan import TpmsNissan
from .TpmsSmartire import TpmsSmartire
from .TpmsToyota import TpmsToyota
from .TpmsTruck import TpmsTruck
from .TpmsTyreguard400 import TpmsTyreguard400

# Misc-source classes
from .TpmsAirpuxem import TpmsAirpuxem
from .TpmsAve import TpmsAve
from .TpmsEezrv import TpmsEezrv
from .TpmsGearHive import TpmsGearHive
from .TpmsImarsT240 import TpmsImarsT240
from .TpmsJansite import TpmsJansite
from .TpmsJansiteSolar import TpmsJansiteSolar
from .TpmsJansiteTy468 import TpmsJansiteTy468
from .TpmsJansiteTy588 import TpmsJansiteTy588
from .TpmsJeep import TpmsJeep
from .TpmsPmv107j import TpmsPmv107j
from .TpmsSchraderMotorcycle import TpmsSchraderMotorcycle

__all__ = [
    # Euro
    "Schraeder",
    "SchraeaderEG53MA4",
    "SchraeaderMRXBC5A4",
    "SchraeaderSMD3MA4",
    "SchraeaderNIS315G3",
    "TPMSBmw",
    "TPMSBmwG3",
    "TPMSCitroen",
    "TPMSMercedesBenz",
    "TPMSRenault",
    "TPMSRenault0435R",
    "TPMSPorsche",
    "TPMSTRW",
    "TPMSHyundaiVDO",
    "TPMSSefisM3",
    "TPMSAbarth124",
    # USA
    "Steelmate",
    "TpmsElantra2012",
    "TpmsFord",
    "TpmsGm",
    "TpmsHonda",
    "TpmsKia",
    "TpmsNissan",
    "TpmsSmartire",
    "TpmsToyota",
    "TpmsTruck",
    "TpmsTyreguard400",
    # Misc
    "TpmsAirpuxem",
    "TpmsAve",
    "TpmsEezrv",
    "TpmsGearHive",
    "TpmsImarsT240",
    "TpmsJansite",
    "TpmsJansiteSolar",
    "TpmsJansiteTy468",
    "TpmsJansiteTy588",
    "TpmsJeep",
    "TpmsPmv107j",
    "TpmsSchraderMotorcycle",
]
