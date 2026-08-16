# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""TSUN Local integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    CONF_ERROR_SCAN_INTERVAL,
    CONF_FAILURE_THRESHOLD,
    CONF_INVERTER_SERIAL_NUMBER,
    CONF_LOGGER_FIRMWARE_VERSION,
    CONF_LOGGER_MAC_ADDRESS,
    CONF_LOGGER_RAW_PROFILE,
    CONF_LOGGER_SN,
    CONF_OFFLINE_SCAN_INTERVAL,
    CONF_PROTOCOL,
    CONF_SCAN_INTERVAL,
    DEFAULT_ERROR_SCAN_INTERVAL,
    DEFAULT_FAILURE_THRESHOLD,
    DEFAULT_OFFLINE_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    PLATFORMS,
)
from .coordinator import TsunCoordinator, get_poll_lock
from .logger_web import async_read_logger_web_data
from .protocols import DEFAULT_PROTOCOL, create_protocol_client

type TsunConfigEntry = ConfigEntry[TsunCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TsunConfigEntry) -> bool:
    """Set up one locally connected TSUN device from a config entry."""
    logger_firmware_version = entry.data.get(CONF_LOGGER_FIRMWARE_VERSION)
    logger_mac_address = entry.data.get(CONF_LOGGER_MAC_ADDRESS)
    logger_raw_profile = entry.data.get(CONF_LOGGER_RAW_PROFILE)
    inverter_serial_number = entry.data.get(CONF_INVERTER_SERIAL_NUMBER)
    logger_data = await async_read_logger_web_data(
        hass, str(entry.data[CONF_HOST])
    )
    logger_firmware_version = (
        logger_data.firmware_version or logger_firmware_version
    )
    logger_mac_address = logger_data.mac_address or logger_mac_address
    logger_raw_profile = logger_data.raw_profile or logger_raw_profile
    inverter_serial_number = (
        logger_data.inverter_serial_number or inverter_serial_number
    )
    data_updates = dict(entry.data)
    if logger_firmware_version is not None:
        data_updates[CONF_LOGGER_FIRMWARE_VERSION] = (
            logger_firmware_version
        )
    if logger_mac_address is not None:
        data_updates[CONF_LOGGER_MAC_ADDRESS] = logger_mac_address
    if logger_raw_profile is not None:
        data_updates[CONF_LOGGER_RAW_PROFILE] = logger_raw_profile
    if inverter_serial_number is not None:
        data_updates[CONF_INVERTER_SERIAL_NUMBER] = inverter_serial_number
    if data_updates != entry.data:
        hass.config_entries.async_update_entry(entry, data=data_updates)

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
        logger_firmware_version,
        logger_mac_address,
        inverter_serial_number,
        logger_raw_profile,
        logger_data.wifi_signal,
        str(entry.data[CONF_HOST]),
    )
    await coordinator.async_config_entry_first_refresh()

    logger_sn = str(entry.data[CONF_LOGGER_SN])
    raw_profile = coordinator.data.get("logger_raw_profile")
    inverter_serial_number = coordinator.data.get("inverter_serial_number")
    firmware_version = coordinator.data.get("logger_firmware_version")
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, logger_sn)},
        manufacturer=MANUFACTURER,
        model=coordinator.client.model,
        model_id=(str(raw_profile) if raw_profile is not None else None),
        name=f"TSUN Local {logger_sn}",
        serial_number=(
            str(inverter_serial_number)
            if inverter_serial_number is not None
            else None
        ),
        sw_version=(
            str(firmware_version) if firmware_version is not None else None
        ),
    )

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TsunConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
