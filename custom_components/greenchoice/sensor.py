from datetime import datetime, date
from decimal import Decimal
from typing import Literal, Iterable

from homeassistant.components.dsmr_reader.definitions import PRICE_EUR_KWH, PRICE_EUR_M3
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ENERGY_KILO_WATT_HOUR, VOLUME_CUBIC_METERS, CURRENCY_EURO)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GreenchoiceDataUpdateCoordinator
from .const import (
    DOMAIN,
    SERVICE_METERSTAND_STROOM,
    SERVICE_METERSTAND_GAS,
    SERVICE_TARIEVEN,
    MANUFACTURER,
    SERVICES,
    MeasurementNames,
    CONF_METERSTAND_STROOM_ENABLED,
    CONF_METERSTAND_GAS_ENABLED,
    CONF_TARIEVEN_ENABLED,
)

SENSORS: dict[Literal["meterstand_stroom", "meterstand_gas", "tarieven"], tuple[SensorEntityDescription, ...]] = {
    SERVICE_METERSTAND_STROOM: (
        SensorEntityDescription(
            key=MeasurementNames.ENERGY_HIGH_IN,
            name="Energie levering hoog tarief",
            icon="mdi:weather-sunset-up",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=MeasurementNames.ENERGY_LOW_IN,
            name="Energie levering laag tarief",
            icon="mdi:weather-sunset-down",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=MeasurementNames.ENERGY_TOTAL_IN,
            name="Energie levering totaal",
            icon="mdi:transmission-tower-export",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=MeasurementNames.ENERGY_HIGH_OUT,
            name="Energie teruglevering hoog tarief",
            icon="mdi:solar-power",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=MeasurementNames.ENERGY_LOW_OUT,
            name="Energie teruglevering laag tarief",
            icon="mdi:solar-power",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=MeasurementNames.ENERGY_TOTAL_OUT,
            name="Energie teruglevering totaal",
            icon="mdi:transmission-tower-import",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
    ),
    SERVICE_METERSTAND_GAS: (
        SensorEntityDescription(
            key=MeasurementNames.GAS_IN,
            name="Gas consumptie",
            icon="mdi:gas-cylinder",
            native_unit_of_measurement=VOLUME_CUBIC_METERS,
            device_class=SensorDeviceClass.GAS,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
    ),
    SERVICE_TARIEVEN: (
        SensorEntityDescription(
            key=MeasurementNames.PRICE_ENERGY_HIGH_IN,
            name="Tarief energie levering hoog tarief",
            icon="mdi:cash-plus",
            native_unit_of_measurement=PRICE_EUR_KWH,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=MeasurementNames.PRICE_ENERGY_LOW_IN,
            name="Tarief energie levering laag tarief",
            icon="mdi:cash-minus",
            native_unit_of_measurement=PRICE_EUR_KWH,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=MeasurementNames.PRICE_ENERGY_HIGH_OUT,
            name="Tarief energie teruglevering hoog tarief",
            icon="mdi:cash-sync",
            native_unit_of_measurement=PRICE_EUR_KWH,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=MeasurementNames.PRICE_ENERGY_LOW_OUT,
            name="Tarief energie teruglevering laag tarief",
            icon="mdi:cash-sync",
            native_unit_of_measurement=PRICE_EUR_KWH,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=MeasurementNames.PRICE_ENERGY_SELL_PRICE,
            name="Tarief terugleververgoeding ",
            icon="mdi:cash-refund",
            native_unit_of_measurement=PRICE_EUR_KWH,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=MeasurementNames.PRICE_GAS_IN,
            name="Tarief gas levering",
            icon="mdi:gas-cylinder",
            native_unit_of_measurement=PRICE_EUR_M3,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=MeasurementNames.COST_ENERGY_YEARLY,
            name="Totale stroomkosten dit jaar",
            icon="mdi:currency-eur",
            native_unit_of_measurement=CURRENCY_EURO,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
        ),
        SensorEntityDescription(
            key=MeasurementNames.COST_GAS_YEARLY,
            name="Totale gaskosten dit jaar",
            icon="mdi:currency-eur",
            native_unit_of_measurement=CURRENCY_EURO,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
        ),
        SensorEntityDescription(
            key=MeasurementNames.COST_TOTAL_YEARLY,
            name="Totale kosten dit jaar",
            icon="mdi:currency-eur",
            native_unit_of_measurement=CURRENCY_EURO,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.TOTAL,
        ),
    )
}


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Greenchoice Sensors based on a config entry."""

    def create_sensor_entities(description: SensorEntityDescription, service_key: str) -> Iterable[GreenchoiceSensorEntity]:
        overeenkomst_id = entry.data['overeenkomst_id']
        yield GreenchoiceSensorEntity(
            coordinator=hass.data[DOMAIN][entry.entry_id],
            description=description,
            name=f"{DOMAIN}_{overeenkomst_id}",
            service_key=service_key
        )

    def __add_entities(service_key: Literal["meterstand_stroom", "meterstand_gas", "tarieven"]):
        async_add_entities(
            sensor_entity
            for description in SENSORS.get(service_key)
            for sensor_entity in create_sensor_entities(description, service_key)
        )

    if entry.options[CONF_METERSTAND_STROOM_ENABLED]:
        __add_entities(SERVICE_METERSTAND_STROOM)

    if entry.options[CONF_METERSTAND_GAS_ENABLED]:
        __add_entities(SERVICE_METERSTAND_GAS)

    if entry.options[CONF_TARIEVEN_ENABLED]:
        __add_entities(SERVICE_TARIEVEN)


class GreenchoiceSensorEntity(CoordinatorEntity, SensorEntity):
    def __init__(self,
                 *,
                 coordinator: GreenchoiceDataUpdateCoordinator,
                 description: SensorEntityDescription,
                 name: str,
                 service_key: str):
        """Initialize Greenchoice sensor"""
        super().__init__(coordinator=coordinator)
        self._service_key = service_key
        overeenkomst_id = coordinator.config_entry.data['overeenkomst_id']
        self.entity_id = f"{SENSOR_DOMAIN}.{name}.{description.key}"
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{overeenkomst_id}_{service_key}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{coordinator.config_entry.entry_id}_{overeenkomst_id}_{service_key}")
            },
            name=f"{SERVICES[service_key]} ({overeenkomst_id})",
            manufacturer=MANUFACTURER,
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        value = self.coordinator.data[self._service_key][self.entity_description.key]
        if isinstance(value, str):
            return value.lower()
        return value

    @property
    def last_reset(self) -> datetime | None:
        if self.state_class == SensorStateClass.TOTAL:
            return datetime(datetime.now().year, 1, 1)
        return None
