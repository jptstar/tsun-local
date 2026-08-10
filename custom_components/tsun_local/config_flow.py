# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Config flow for TSUN Local devices using protocol 1511."""

from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import (
    CONF_LOGGER_SN,
    CONF_OFFLINE_SCAN_INTERVAL,
    CONF_SCAN_INTERVAL,
    DEFAULT_OFFLINE_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_OFFLINE_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
    MIN_OFFLINE_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .protocol import TsunClient


async def _validate_input(data: dict[str, Any]) -> None:
    client = TsunClient(data[CONF_HOST], data[CONF_PORT], data[CONF_LOGGER_SN])
    await client.async_read_all()


CONNECTION_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_LOGGER_SN): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=0xFFFFFFFF)
        ),
    }
)

RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): NumberSelector(
            NumberSelectorConfig(
                min=MIN_SCAN_INTERVAL,
                max=MAX_SCAN_INTERVAL,
                step=1,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="s",
            )
        ),
        vol.Required(
            CONF_OFFLINE_SCAN_INTERVAL, default=DEFAULT_OFFLINE_SCAN_INTERVAL
        ): NumberSelector(
            NumberSelectorConfig(
                min=MIN_OFFLINE_SCAN_INTERVAL,
                max=MAX_OFFLINE_SCAN_INTERVAL,
                step=60,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="s",
            )
        ),
    }
)


class TsunConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            unique_id = str(user_input[CONF_LOGGER_SN])
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            try:
                await _validate_input(user_input)
            except (TimeoutError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "invalid_response"
            else:
                return self.async_create_entry(
                    title=f"TSUN Local ({unique_id})", data=user_input
                )

        return self.async_show_form(
            step_id="user", data_schema=CONNECTION_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Allow the IP address and TCP port to be changed from Home Assistant."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            updated_data = {**entry.data, **user_input}
            try:
                await _validate_input(updated_data)
            except (TimeoutError, asyncio.TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "invalid_response"
            else:
                await self.async_set_unique_id(str(entry.data[CONF_LOGGER_SN]))
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                    reload_even_if_entry_is_unchanged=False,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                RECONFIGURE_SCHEMA, entry.data
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> TsunOptionsFlow:
        """Return the options flow."""
        return TsunOptionsFlow()


class TsunOptionsFlow(config_entries.OptionsFlowWithReload):
    """Handle polling options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA,
                {
                    CONF_SCAN_INTERVAL: self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                    CONF_OFFLINE_SCAN_INTERVAL: self.config_entry.options.get(
                        CONF_OFFLINE_SCAN_INTERVAL,
                        DEFAULT_OFFLINE_SCAN_INTERVAL,
                    ),
                },
            ),
        )
