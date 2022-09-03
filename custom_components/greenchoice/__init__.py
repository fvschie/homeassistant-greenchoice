from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    PLATFORM_SCHEMA
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_OVEREENKOMST_ID,
    CONFIGFLOW_VERSION,
    LOGGER,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DEFAULT_NAME
)
from .greenchoice_api import GreenchoiceApi, GreenchoiceOvereenkomst, GreenchoiceError, GreenchoiceApiData

PLATFORMS = (SENSOR_DOMAIN,)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_USERNAME, default=CONF_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD, default=CONF_USERNAME): cv.string,
    vol.Optional(CONF_OVEREENKOMST_ID, default=CONF_OVEREENKOMST_ID): cv.string,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Greenchoice Sensor from a config entry."""

    scan_interval = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
    coordinator = GreenchoiceDataUpdateCoordinator(hass, scan_interval)
    try:
        await coordinator.async_config_entry_first_refresh()
    except ConfigEntryNotReady:
        raise

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    if config_entry.version <= 1:
        LOGGER.warning(
            "Impossible to migrate config version from version %s to version %s.\r\nPlease consider to delete and re-add the integration.",
            config_entry.version,
            CONFIGFLOW_VERSION,
        )
        return False


class GreenchoiceDataUpdateCoordinator(DataUpdateCoordinator[GreenchoiceApiData]):
    """Class to manage fetching Greenchoice API data from single endpoint."""

    config_entry: ConfigEntry

    def __init__(
            self,
            hass: HomeAssistant,
            scan_interval: timedelta,
    ) -> None:
        """Initialize global Greenchoice data updater."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )

    async def _async_update_data(self) -> GreenchoiceApiData:
        """Fetch data from Greenchoice API."""
        try:
            api = GreenchoiceApi(self.config_entry.data[CONF_USERNAME], self.config_entry.data[CONF_PASSWORD])
            await self.hass.async_add_executor_job(api.login)
            data = await self.hass.async_add_executor_job(api.get_update, int(self.config_entry.data[CONF_OVEREENKOMST_ID]))
            if data is None:
                raise GreenchoiceError("Unable to retrieve data")
            return data
        except GreenchoiceError as err:
            raise UpdateFailed(err) from err
