from __future__ import annotations

import logging
from typing import Final, Dict

DOMAIN: Final = "greenchoice"

MANUFACTURER: Final = "Greenchoice"
CONFIGFLOW_VERSION = 1
LOGGER = logging.getLogger(__package__)

DEFAULT_NAME = 'Energieverbruik'
DEFAULT_SCAN_INTERVAL_MINUTES = 60

SERVICE_METERSTAND_STROOM = "meterstand_stroom"
SERVICE_METERSTAND_GAS = "meterstand_gas"
SERVICE_TARIEVEN = "tarieven"

SERVICES: Dict[str,str] = {
    SERVICE_METERSTAND_STROOM: "Greenchoice meterstanden stroom",
    SERVICE_METERSTAND_GAS: "Greenchoice meterstanden gas",
    SERVICE_TARIEVEN: "Greenchoice tarieven"
}

MEASUREMENT_TYPES = {
    1: 'consumption_high',
    2: 'consumption_low',
    3: 'return_high',
    4: 'return_low'
}

CONF_OVEREENKOMST_ID = 'overeenkomst_id'

API_URL = "https://mijn.greenchoice.nl"
