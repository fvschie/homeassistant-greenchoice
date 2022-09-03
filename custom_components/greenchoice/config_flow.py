"""Config flow for Greenchoice Sensor integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode, SelectOptionDict

from . import GreenchoiceApi, GreenchoiceError
from .const import (
    CONF_OVEREENKOMST_ID,
    CONFIGFLOW_VERSION,
    DOMAIN, )


class GreenchoiceFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Greenchoice Sensor."""

    VERSION = CONFIGFLOW_VERSION

    data = None
    api = None

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
