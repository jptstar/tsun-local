# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Config flow for TSUN Local."""

from __future__ import annotations

import asyncio
from ipaddress import IPv4Network, ip_network
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import network
from homeassistant.components.network import MDNS_TARGET_IP
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_LOGGER_SN,
    CONF_OFFLINE_SCAN_INTERVAL,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    DEFAULT_OFFLINE_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_OFFLINE_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
    MIN_OFFLINE_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .discovery import async_scan_hosts
from .protocols import DEFAULT_PROTOCOL, create_protocol_client

CONFIGURABLE_PROTOCOLS = ("1511", "02b0")


async def _validate_input(data: dict[str, Any]) -> str:
    client = create_protocol_client(
        data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
        data[CONF_HOST],
        data[CONF_PORT],
        data[CONF_LOGGER_SN],
    )
    await client.async_read_all()
    return client.protocol_name


def _protocol_selector() -> SelectSelector:
    """Return the translated device-family selector."""
    return SelectSelector(
        SelectSelectorConfig(
            options=list(CONFIGURABLE_PROTOCOLS),
            mode=SelectSelectorMode.DROPDOWN,
            translation_key="protocol",
        )
    )


def _connection_schema(discovered_hosts: list[str] | None = None) -> vol.Schema:
    """Build a manual or discovery-assisted connection form."""
    host_field: Any = str
    if discovered_hosts:
        host_field = SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value=host, label=host)
                    for host in discovered_hosts
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
    return vol.Schema(
        {
            vol.Required(CONF_HOST): host_field,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
            ),
            vol.Required(CONF_PROTOCOL): _protocol_selector(),
            vol.Required(CONF_LOGGER_SN): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=0xFFFFFFFF)
            ),
        }
    )


RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Required(CONF_PROTOCOL): _protocol_selector(),
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


async def _async_get_discovery_network(hass: HomeAssistant) -> IPv4Network:
    """Return a bounded local IPv4 network for an on-demand scan."""
    local_ip = await network.async_get_source_ip(hass, MDNS_TARGET_IP)
    prefix = 24
    for adapter in await network.async_get_adapters(hass):
        if not adapter["enabled"]:
            continue
        for ipv4 in adapter["ipv4"]:
            if ipv4["address"] == local_ip:
                prefix = max(ipv4["network_prefix"], 24)
                break
    discovered_network = ip_network(f"{local_ip}/{prefix}", strict=False)
    if not isinstance(discovered_network, IPv4Network):
        raise ValueError("No IPv4 network available for discovery")
    return discovered_network


class TsunConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the configuration flow."""
        self._discovered_hosts: list[str] | None = None

    async def _async_create_device(
        self, user_input: dict[str, Any]
    ) -> FlowResult | str:
        """Validate a device and return an entry or a translated error key."""
        try:
            detected_protocol = await _validate_input(user_input)
        except (TimeoutError, asyncio.TimeoutError, ConnectionError, OSError):
            return "cannot_connect"
        except Exception:
            return "invalid_response"

        unique_id = str(user_input[CONF_LOGGER_SN])
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        entry_data = {
            **user_input,
            CONF_PROTOCOL: detected_protocol,
        }
        return self.async_create_entry(
            title=f"TSUN Local ({unique_id})", data=entry_data
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Offer manual setup or a user-initiated local network search."""
        return self.async_show_menu(
            step_id="user", menu_options=["discover", "manual"]
        )

    async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle manual setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            result = await self._async_create_device(user_input)
            if not isinstance(result, str):
                return result
            errors["base"] = result

        return self.async_show_form(
            step_id="manual", data_schema=_connection_schema(), errors=errors
        )

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Search the local /24 on demand, then configure a selected host."""
        if self._discovered_hosts is None:
            try:
                discovery_network = await _async_get_discovery_network(self.hass)
                self._discovered_hosts = await async_scan_hosts(
                    discovery_network.hosts(), DEFAULT_PORT
                )
            except (OSError, RuntimeError, ValueError):
                return self.async_abort(reason="no_devices_found")
            if not self._discovered_hosts:
                return self.async_abort(reason="no_devices_found")

        errors: dict[str, str] = {}
        if user_input is not None:
            result = await self._async_create_device(user_input)
            if not isinstance(result, str):
                return result
            errors["base"] = result

        return self.async_show_form(
            step_id="discover",
            data_schema=_connection_schema(self._discovered_hosts),
            errors=errors,
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
