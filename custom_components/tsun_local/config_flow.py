# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Config flow for TSUN Local."""

from __future__ import annotations

import asyncio
from ipaddress import IPv4Network
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import network
from homeassistant.components.network import MDNS_TARGET_IP
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
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
    CONF_DISCOVERY_NETWORK,
    CONF_ERROR_SCAN_INTERVAL,
    CONF_FAILURE_THRESHOLD,
    CONF_INVERTER_SERIAL_NUMBER,
    CONF_LOGGER_FIRMWARE_VERSION,
    CONF_LOGGER_MAC_ADDRESS,
    CONF_LOGGER_SN,
    CONF_OFFLINE_SCAN_INTERVAL,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    DEFAULT_ERROR_SCAN_INTERVAL,
    DEFAULT_FAILURE_THRESHOLD,
    DEFAULT_OFFLINE_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_ERROR_SCAN_INTERVAL,
    MAX_FAILURE_THRESHOLD,
    MAX_OFFLINE_SCAN_INTERVAL,
    MAX_SCAN_INTERVAL,
    MIN_ERROR_SCAN_INTERVAL,
    MIN_FAILURE_THRESHOLD,
    MIN_OFFLINE_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)
from .coordinator import get_poll_lock
from .discovery import (
    async_discover_devices,
    bounded_ipv4_network,
    parse_discovery_network,
)
from .logger_web import async_read_logger_web_data
from .protocols import (
    DEFAULT_PROTOCOL,
    FORCE_PROTOCOL,
    SUPPORTED_PROTOCOLS,
    create_protocol_client,
    protocol_from_firmware,
)


_CONTEXT_CONTINUE_DISCOVERY = "tsun_continue_discovery"
_CONTEXT_DISCOVERY_NETWORKS = "tsun_discovery_networks"
_CONTEXT_DISCOVERY_PORT = "tsun_discovery_port"
_CONTEXT_EXCLUDED_HOSTS = "tsun_excluded_hosts"
_SOURCE_CONTINUE_DISCOVERY = "tsun_continue_discovery"
_FORCE_PROTOCOL_DETECTION = "force"


async def _validate_input(hass: HomeAssistant, data: dict[str, Any]) -> str:
    client = create_protocol_client(
        data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
        data[CONF_HOST],
        data[CONF_PORT],
        data[CONF_LOGGER_SN],
    )
    async with get_poll_lock(hass):
        await client.async_read_all()
    return client.protocol_name


def _connection_schema(
    discovered_hosts: list[str] | None = None,
    port: int = DEFAULT_PORT,
    *,
    request_logger_sn: bool = False,
    protocol_selector: bool = False,
) -> vol.Schema:
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
    schema: dict[vol.Marker, Any] = {
        vol.Required(CONF_HOST): host_field,
        vol.Required(CONF_PORT, default=port): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
    }
    if protocol_selector:
        schema[vol.Required(CONF_PROTOCOL, default=DEFAULT_PROTOCOL)] = (
            SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(
                            value=DEFAULT_PROTOCOL,
                            label="Automatic (firmware)",
                        ),
                        SelectOptionDict(
                            value=_FORCE_PROTOCOL_DETECTION,
                            label="Force protocol probing",
                        ),
                        *(
                            SelectOptionDict(
                                value=protocol_name,
                                label=protocol_name.upper(),
                            )
                            for protocol_name in SUPPORTED_PROTOCOLS
                        ),
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )
        )
    if request_logger_sn:
        schema[vol.Required(CONF_LOGGER_SN)] = vol.All(
            vol.Coerce(int), vol.Range(min=1, max=0xFFFFFFFF)
        )
    return vol.Schema(schema)


def _discovery_network_schema(
    suggested_network: str | None,
    port: int,
) -> vol.Schema:
    """Build the fallback form for routed or containerized installations."""
    network_key = vol.Required(CONF_DISCOVERY_NETWORK)
    if suggested_network is not None:
        network_key = vol.Required(
            CONF_DISCOVERY_NETWORK, default=suggested_network
        )
    return vol.Schema(
        {
            network_key: str,
            vol.Required(CONF_PORT, default=port): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=65535)
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
            CONF_ERROR_SCAN_INTERVAL, default=DEFAULT_ERROR_SCAN_INTERVAL
        ): NumberSelector(
            NumberSelectorConfig(
                min=MIN_ERROR_SCAN_INTERVAL,
                max=MAX_ERROR_SCAN_INTERVAL,
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
        vol.Required(
            CONF_FAILURE_THRESHOLD, default=DEFAULT_FAILURE_THRESHOLD
        ): NumberSelector(
            NumberSelectorConfig(
                min=MIN_FAILURE_THRESHOLD,
                max=MAX_FAILURE_THRESHOLD,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        ),
    }
)


async def _async_get_discovery_networks(
    hass: HomeAssistant,
) -> list[IPv4Network]:
    """Return visible networks plus networks learned from TSUN entries."""
    discovered_networks: set[IPv4Network] = set()
    for adapter in await network.async_get_adapters(hass):
        if not adapter["enabled"]:
            continue
        for ipv4 in adapter["ipv4"]:
            if discovered_network := bounded_ipv4_network(
                ipv4["address"], ipv4["network_prefix"]
            ):
                discovered_networks.add(discovered_network)

    # A routed VLAN does not necessarily appear as a Home Assistant network
    # adapter. Once one TSUN on that VLAN has been configured manually, reuse
    # its /24 automatically for every later discovery run.
    for entry in hass.config_entries.async_entries(DOMAIN):
        if host := entry.data.get(CONF_HOST):
            try:
                discovered_network = bounded_ipv4_network(str(host), 24)
            except ValueError:
                continue
            if discovered_network is not None:
                discovered_networks.add(discovered_network)

    if not discovered_networks:
        local_ip = await network.async_get_source_ip(hass, MDNS_TARGET_IP)
        if discovered_network := bounded_ipv4_network(local_ip, 24):
            discovered_networks.add(discovered_network)

    return sorted(
        discovered_networks, key=lambda item: int(item.network_address)
    )


class TsunConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the configuration flow."""
        self._discovered_hosts: list[str] | None = None
        self._discovery_networks: list[IPv4Network] | None = None
        self._discovery_port = DEFAULT_PORT
        self._excluded_hosts: set[str] = set()
        self._detected_logger_sn: int | None = None
        self._logger_firmware_version: str | None = None
        self._logger_mac_address: str | None = None
        self._inverter_serial_number: str | None = None
        self._logger_sn_required = False
        self._suggested_network: str | None = None
        self._continue_discovery_host: str | None = None

    def _unconfigured_hosts(self, hosts: list[str]) -> list[str]:
        """Return discovered hosts not already assigned to a config entry."""
        configured_hosts = {
            str(entry.data[CONF_HOST])
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if CONF_HOST in entry.data
        }
        excluded_hosts = configured_hosts | self._excluded_hosts
        return [host for host in hosts if host not in excluded_hosts]

    async def _async_prepare_next_discovery(
        self, current_host: str
    ) -> tuple[config_entries.FlowType, str] | None:
        """Start a fresh scan to continue adding remaining devices."""
        excluded_hosts = self._excluded_hosts | {current_host}
        next_result = await self.hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                # A second SOURCE_USER flow for the same integration is
                # rejected while async_on_create_entry is still finalizing
                # this one. A dedicated source keeps the returned flow alive
                # for the frontend's next_flow transition.
                "source": _SOURCE_CONTINUE_DISCOVERY,
                _CONTEXT_CONTINUE_DISCOVERY: True,
                _CONTEXT_DISCOVERY_NETWORKS: [
                    str(network) for network in self._discovery_networks or []
                ],
                _CONTEXT_DISCOVERY_PORT: self._discovery_port,
                _CONTEXT_EXCLUDED_HOSTS: sorted(excluded_hosts),
            },
        )
        if (
            next_result.get("type") not in {"abort", "create_entry"}
            and (flow_id := next_result.get("flow_id"))
        ):
            return (config_entries.FlowType.CONFIG_FLOW, flow_id)
        return None

    async def _async_create_device(
        self,
        user_input: dict[str, Any],
        *,
        continue_discovery: bool = False,
    ) -> FlowResult | str:
        """Validate a device and return an entry or a translated error key."""
        entry_input = dict(user_input)
        detection_mode = str(
            entry_input.pop(CONF_PROTOCOL, DEFAULT_PROTOCOL)
        ).lower()
        automatically_detected = CONF_LOGGER_SN not in entry_input
        if automatically_detected:
            logger_data = await async_read_logger_web_data(
                self.hass,
                str(entry_input[CONF_HOST]),
                int(entry_input[CONF_PORT]),
            )
            logger_sn = logger_data.logger_sn
            self._logger_firmware_version = logger_data.firmware_version
            self._logger_mac_address = logger_data.mac_address
            self._inverter_serial_number = logger_data.inverter_serial_number
            if logger_sn is None:
                self._logger_sn_required = True
                return "cannot_detect_logger_sn"
            entry_input[CONF_LOGGER_SN] = logger_sn
            self._detected_logger_sn = logger_sn

        if detection_mode == _FORCE_PROTOCOL_DETECTION:
            entry_input[CONF_PROTOCOL] = FORCE_PROTOCOL
        elif detection_mode in SUPPORTED_PROTOCOLS:
            entry_input[CONF_PROTOCOL] = detection_mode
        else:
            firmware_protocol = protocol_from_firmware(
                self._logger_firmware_version
            )
            if firmware_protocol is None:
                return "unknown_firmware"
            entry_input[CONF_PROTOCOL] = firmware_protocol

        try:
            detected_protocol = await _validate_input(self.hass, entry_input)
        except (TimeoutError, asyncio.TimeoutError, ConnectionError, OSError):
            return "cannot_connect"
        except Exception:
            if automatically_detected:
                self._logger_sn_required = True
            return "invalid_response"

        unique_id = str(entry_input[CONF_LOGGER_SN])
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()
        entry_data = {
            **entry_input,
            CONF_PROTOCOL: detected_protocol,
        }
        if self._logger_firmware_version is not None:
            entry_data[CONF_LOGGER_FIRMWARE_VERSION] = (
                self._logger_firmware_version
            )
        if self._logger_mac_address is not None:
            entry_data[CONF_LOGGER_MAC_ADDRESS] = self._logger_mac_address
        if self._inverter_serial_number is not None:
            entry_data[CONF_INVERTER_SERIAL_NUMBER] = (
                self._inverter_serial_number
            )
        if continue_discovery:
            self._discovery_port = entry_input[CONF_PORT]
            # Starting another flow before this one has finished causes Home
            # Assistant to reject it as already_in_progress. Defer it to
            # async_on_create_entry, which runs after this entry exists.
            self._continue_discovery_host = str(entry_input[CONF_HOST])
        return self.async_create_entry(
            title=f"TSUN Local ({unique_id})",
            data=entry_data,
        )

    async def async_on_create_entry(self, result: FlowResult) -> FlowResult:
        """Continue discovery only after the current flow has finalized."""
        if self._continue_discovery_host is None:
            return result
        next_flow = await self._async_prepare_next_discovery(
            self._continue_discovery_host
        )
        if next_flow is not None:
            result["next_flow"] = next_flow
        return result

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Offer manual setup or a user-initiated local network search."""
        if self.context.get(_CONTEXT_CONTINUE_DISCOVERY):
            self._discovery_port = int(
                self.context.get(_CONTEXT_DISCOVERY_PORT, DEFAULT_PORT)
            )
            self._excluded_hosts.update(
                str(host)
                for host in self.context.get(_CONTEXT_EXCLUDED_HOSTS, [])
            )
            serialized_networks = self.context.get(
                _CONTEXT_DISCOVERY_NETWORKS, []
            )
            if serialized_networks:
                self._discovery_networks = [
                    parse_discovery_network(str(discovered_network))
                    for discovered_network in serialized_networks
                ]
            return await self.async_step_discover()
        return self.async_show_menu(
            step_id="user", menu_options=["discover", "manual"]
        )

    async def async_step_tsun_continue_discovery(
        self, discovery_info: dict[str, Any] | None = None
    ) -> FlowResult:
        """Resume discovery after another TSUN entry was created."""
        return await self.async_step_user()

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
            step_id="manual",
            data_schema=self.add_suggested_values_to_schema(
                _connection_schema(
                    request_logger_sn=self._logger_sn_required,
                    protocol_selector=True,
                ),
                {
                    **(
                        {CONF_LOGGER_SN: self._detected_logger_sn}
                        if self._detected_logger_sn is not None
                        else {}
                    ),
                    **(user_input or {}),
                },
            ),
            errors=errors,
        )

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Search every local /24 exposed by Home Assistant on demand."""
        if self._discovered_hosts is None:
            discovered_hosts: list[str] = []
            try:
                discovery_networks = self._discovery_networks
                if discovery_networks is None:
                    discovery_networks = await _async_get_discovery_networks(
                        self.hass
                    )
                    self._discovery_networks = discovery_networks
                if discovery_networks:
                    self._suggested_network = str(discovery_networks[0])
                discovered_hosts = await async_discover_devices(
                    discovery_networks, self._discovery_port
                )
                self._discovered_hosts = self._unconfigured_hosts(discovered_hosts)
            except (HomeAssistantError, OSError, RuntimeError, ValueError):
                self._discovered_hosts = []
            if not self._discovered_hosts:
                if discovered_hosts:
                    return self.async_abort(reason="all_devices_configured")
                return await self.async_step_discover_network()

        errors: dict[str, str] = {}
        if user_input is not None:
            result = await self._async_create_device(
                user_input, continue_discovery=True
            )
            if not isinstance(result, str):
                return result
            errors["base"] = result

        return self.async_show_form(
            step_id="discover",
            data_schema=self.add_suggested_values_to_schema(
                _connection_schema(
                    self._discovered_hosts,
                    self._discovery_port,
                    request_logger_sn=self._logger_sn_required,
                ),
                {
                    **(
                        {CONF_LOGGER_SN: self._detected_logger_sn}
                        if self._detected_logger_sn is not None
                        else {}
                    ),
                    **(user_input or {}),
                },
            ),
            errors=errors,
        )

    async def async_step_discover_network(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Allow a routed LAN or VLAN to be supplied when automatic scan fails."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                discovery_network = parse_discovery_network(
                    user_input[CONF_DISCOVERY_NETWORK]
                )
                self._discovery_port = user_input[CONF_PORT]
                self._suggested_network = str(discovery_network)
                self._discovery_networks = [discovery_network]
                discovered_hosts = await async_discover_devices(
                    [discovery_network], self._discovery_port
                )
                self._discovered_hosts = self._unconfigured_hosts(discovered_hosts)
            except ValueError:
                errors["base"] = "invalid_network"
            except (OSError, RuntimeError):
                errors["base"] = "no_devices_found"
            else:
                if self._discovered_hosts:
                    return await self.async_step_discover()
                if discovered_hosts:
                    return self.async_abort(reason="all_devices_configured")
                errors["base"] = "no_devices_found"

        return self.async_show_form(
            step_id="discover_network",
            data_schema=_discovery_network_schema(
                self._suggested_network, self._discovery_port
            ),
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
                await _validate_input(self.hass, updated_data)
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
                    CONF_ERROR_SCAN_INTERVAL: self.config_entry.options.get(
                        CONF_ERROR_SCAN_INTERVAL,
                        DEFAULT_ERROR_SCAN_INTERVAL,
                    ),
                    CONF_OFFLINE_SCAN_INTERVAL: self.config_entry.options.get(
                        CONF_OFFLINE_SCAN_INTERVAL,
                        DEFAULT_OFFLINE_SCAN_INTERVAL,
                    ),
                    CONF_FAILURE_THRESHOLD: self.config_entry.options.get(
                        CONF_FAILURE_THRESHOLD,
                        DEFAULT_FAILURE_THRESHOLD,
                    ),
                },
            ),
        )
