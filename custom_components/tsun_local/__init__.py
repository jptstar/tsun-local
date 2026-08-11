# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""TSUN Local integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from .const import (
    CONF_ERROR_SCAN_INTERVAL,
    CONF_FAILURE_THRESHOLD,
    CONF_LOGGER_SN,
    CONF_OFFLINE_SCAN_INTERVAL,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    DEFAULT_ERROR_SCAN_INTERVAL,
    DEFAULT_FAILURE_THRESHOLD,
    DEFAULT_OFFLINE_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
)
from .coordinator import TsunCoordinator, get_poll_lock
from .protocols import DEFAULT_PROTOCOL, create_protocol_client

type TsunConfigEntry = ConfigEntry[TsunCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TsunConfigEntry) -> bool:
    """Set up one locally connected TSUN device from a config entry."""
    client = create_protocol_client(
        entry.data.get(CONF_PROTOCOL, DEFAULT_PROTOCOL),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data[CONF_LOGGER_SN],
    )
    interval = int(
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    error_interval = int(
        entry.options.get(CONF_ERROR_SCAN_INTERVAL, DEFAULT_ERROR_SCAN_INTERVAL)
    )
    offline_interval = int(
        entry.options.get(
            CONF_OFFLINE_SCAN_INTERVAL, DEFAULT_OFFLINE_SCAN_INTERVAL
        )
    )
    failure_threshold = int(
        entry.options.get(CONF_FAILURE_THRESHOLD, DEFAULT_FAILURE_THRESHOLD)
    )
    coordinator = TsunCoordinator(
        hass,
        entry,
        client,
        interval,
        error_interval,
        offline_interval,
        failure_threshold,
        get_poll_lock(hass),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TsunConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
