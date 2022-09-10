from __future__ import annotations

import logging
from typing import Final, Dict

from homeassistant.backports.enum import StrEnum

DOMAIN: Final = "greenchoice"

MANUFACTURER: Final = "Greenchoice"
CONFIGFLOW_VERSION = 1
LOGGER = logging.getLogger(__package__)

DEFAULT_NAME = 'Energieverbruik'

SERVICE_METERSTAND_STROOM = "meterstand_stroom"
SERVICE_METERSTAND_GAS = "meterstand_gas"
SERVICE_TARIEVEN = "tarieven"

SERVICES: Dict[str, str] = {
    SERVICE_METERSTAND_STROOM: "Greenchoice meterstanden stroom",
    SERVICE_METERSTAND_GAS: "Greenchoice meterstanden gas",
    SERVICE_TARIEVEN: "Greenchoice tarieven"
}


class MeasurementNames(StrEnum):
    # Meterstanden stroom
    ENERGY_HIGH_IN = 'stroom_hoog_in'
    ENERGY_HIGH_OUT = 'stroom_hoog_uit'
    ENERGY_LOW_IN = 'stroom_laag_in'
    ENERGY_LOW_OUT = 'stroom_laag_uit'
    ENERGY_TOTAL_IN = 'stroom_totaal_in'
    ENERGY_TOTAL_OUT = 'stroom_totaal_uit'
    ENERGY_MEASUREMENT_DATE = 'measurement_date_electricity'

    # Meterstanden gas
    GAS_IN = 'gas_in'
    GAS_MEASUREMENT_DATE = 'measurement_date_gas'

    # Tariffs and costs
    PRICE_ENERGY_LOW_IN = 'tarief_stroom_laag_in'
    PRICE_ENERGY_LOW_OUT = 'tarief_stroom_laag_uit'
    PRICE_ENERGY_HIGH_IN = 'tarief_stroom_hoog_in'
    PRICE_ENERGY_HIGH_OUT = 'tarief_stroom_hoog_uit'
    PRICE_ENERGY_SELL_PRICE = 'tarief_stroom_terugleververgoeding'
    PRICE_GAS_IN = 'tarief_gas_in'
    COST_ENERGY_YEARLY = 'kosten_stroom_jaar'
    COST_GAS_YEARLY = 'kosten_gas_jaar'
    COST_TOTAL_YEARLY = 'kosten_totaal_jaar'


MEASUREMENT_TYPES = {
    1: 'consumption_high',
    2: 'consumption_low',
    3: 'return_high',
    4: 'return_low'
}

DEFAULT_SCAN_INTERVAL_MINUTES = 60
DEFAULT_METERSTAND_STROOM_ENABLED = True
DEFAULT_METERSTAND_GAS_ENABLED = True
DEFAULT_TARIEVEN_ENABLED = True

CONF_OVEREENKOMST_ID = 'overeenkomst_id'
CONF_METERSTAND_STROOM_ENABLED = 'meterstand_stroom_enabled'
CONF_METERSTAND_GAS_ENABLED = 'meterstand_gas_enabled'
CONF_TARIEVEN_ENABLED = 'tarieven_enabled'

API_URL = "https://mijn.greenchoice.nl"
