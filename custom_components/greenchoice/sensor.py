from datetime import datetime, date
from decimal import Decimal
from typing import Literal

from homeassistant.components.dsmr_reader.definitions import PRICE_EUR_KWH, PRICE_EUR_M3
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (ENERGY_KILO_WATT_HOUR, VOLUME_CUBIC_METERS)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, GreenchoiceDataUpdateCoordinator
from .const import (
    SERVICE_METERSTAND_STROOM,
    SERVICE_METERSTAND_GAS,
    SERVICE_TARIEVEN,
    MANUFACTURER,
    SERVICES,
)

SENSORS: dict[Literal["meterstand_stroom", "meterstand_gas", "tarieven"], tuple[SensorEntityDescription, ...]] = {
    SERVICE_METERSTAND_STROOM: (
        SensorEntityDescription(
            key="energy_consumption_high",
            name="Energy consumption high tariff",
            icon="mdi:weather-sunset-up",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key="energy_consumption_low",
            name="Energy consumption low tariff",
            icon="mdi:weather-sunset-down",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key="energy_consumption_total",
            name="Total energy consumption",
            icon="mdi:transmission-tower-export",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key="energy_return_high",
            name="Energy return high tariff",
            icon="mdi:solar-power",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key="energy_return_low",
            name="Energy return low tariff",
            icon="mdi:solar-power",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key="energy_return_total",
            name="Total energy return",
            icon="mdi:transmission-tower-import",
            native_unit_of_measurement=ENERGY_KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
    ),
    SERVICE_METERSTAND_GAS: (
        SensorEntityDescription(
            key="gas_consumption",
            name="Gas consumption",
            icon="mdi:fire",
            native_unit_of_measurement=VOLUME_CUBIC_METERS,
            device_class=SensorDeviceClass.GAS,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
    ),
    SERVICE_TARIEVEN: (
        SensorEntityDescription(
            key="stroom_hoog_all_in",
            name="Levering stroom hoog tarief all-in",
            icon="mdi:cash-plus",
            native_unit_of_measurement=PRICE_EUR_KWH,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key="stroom_laag_all_in",
            name="Levering stroom laag tarief all-in",
            icon="mdi:cash-minus",
            native_unit_of_measurement=PRICE_EUR_KWH,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key="gas_all_in",
            name="Levering gas tarief all-in",
            icon="mdi:fire",
            native_unit_of_measurement=PRICE_EUR_M3,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    )
}


async def async_setup_entry(
        hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Greenchoice Sensors based on a config entry."""

    def create_sensor_entities(description: SensorEntityDescription, service_key: str):
        yield GreenchoiceSensorEntity(
            coordinator=hass.data[DOMAIN][entry.entry_id],
            description=description,
            name=entry.title,
            service_key=service_key
        )

    async_add_entities(
        sensor_entity
        for service_key, service_sensors in SENSORS.items()
        for description in service_sensors
        for sensor_entity in create_sensor_entities(description, service_key)
    )


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
