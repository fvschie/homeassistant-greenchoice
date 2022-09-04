"""Config flow for Greenchoice Sensor integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_SCAN_INTERVAL,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode, SelectOptionDict

from . import GreenchoiceApi, GreenchoiceError, DEFAULT_SCAN_INTERVAL_MINUTES
from .const import (
    CONF_OVEREENKOMST_ID,
    CONFIGFLOW_VERSION,
    DOMAIN, )


class GreenchoiceFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Greenchoice Sensor."""

    VERSION = CONFIGFLOW_VERSION

    data = None
    api = None

    @staticmethod
    @callback
    def async_get_options_flow(
            config_entry: ConfigEntry,
    ) -> GreenchoiceSensorOptionsFlowHandler:
        """Get the options flow for this handler."""
        return GreenchoiceSensorOptionsFlowHandler(config_entry)

    async def async_step_user(
            self, user_input=None, errors: dict[str, str] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""

        errors = {}
        if user_input is not None:
            try:
                api = GreenchoiceApi(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
                await self.hass.async_add_executor_job(api.login)
            except GreenchoiceError:
                errors["base"] = "login_failure"
            else:
                self.data = user_input
                self.data[CONF_OVEREENKOMST_ID] = None
                self.api = api
                return await self.async_step_setup_overeenkomst()

        schema = vol.Schema({
            vol.Required(CONF_USERNAME): str,
            vol.Required(CONF_PASSWORD): str
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_setup_overeenkomst(
            self,
            user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle setup flow Greenchoice sensor."""
        errors = {}

        print(f"Checking if we have user input: {user_input}")
        if user_input is not None:
            self.data[CONF_OVEREENKOMST_ID] = user_input[CONF_OVEREENKOMST_ID]
            return self.async_create_entry(title="Greenchoice API", data=self.data)

        overeenkomsten = await self.hass.async_add_executor_job(self.api.get_overeenkomsten)
        options = list[SelectOptionDict]()
        for overeenkomst in overeenkomsten:
            options.append(SelectOptionDict(value=str(overeenkomst.overeenkomst_id), label=str(overeenkomst)))
        schema = vol.Schema({
            vol.Required(CONF_OVEREENKOMST_ID): SelectSelector(SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN))
        })
        return self.async_show_form(step_id="setup_overeenkomst", data_schema=schema, errors=errors)


class GreenchoiceSensorOptionsFlowHandler(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
            self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Convert scan interval to integer
            options_data = {CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])}
            return self.async_create_entry(title="", data=options_data)

        options = list[SelectOptionDict]()
        options.append(SelectOptionDict(value="15", label="elk kwartier"))
        options.append(SelectOptionDict(value="60", label="elk uur"))
        options.append(SelectOptionDict(value="1440", label="elke dag"))
        options.append(SelectOptionDict(value="10080", label="elke week"))
        schema = vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=str(self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES))
            ): SelectSelector(SelectSelectorConfig(options=options, mode=SelectSelectorMode.LIST))
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )
