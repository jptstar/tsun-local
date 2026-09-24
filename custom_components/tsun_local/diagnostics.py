# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Privacy-safe diagnostics support for TSUN Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from . import TsunConfigEntry
from .cloud_guard import async_read_cloud_guard_capabilities
from .const import (
    CONF_INVERTER_SERIAL_NUMBER,
    CONF_LOGGER_MAC_ADDRESS,
    CONF_LOGGER_SN,
)
from .protocols import protocol_from_firmware

TO_REDACT = {
    CONF_HOST,
    CONF_INVERTER_SERIAL_NUMBER,
    CONF_LOGGER_SN,
    CONF_LOGGER_MAC_ADDRESS,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: TsunConfigEntry
) -> dict[str, Any]:
    """Return diagnostics with the network address and logger number redacted."""
    coordinator = entry.runtime_data
    firmware_version = coordinator.data.get("logger_firmware_version")
    firmware_protocol_hint = protocol_from_firmware(
        str(firmware_version) if firmware_version is not None else None
    )
    measurements = {
        key: value
        for key, value in (coordinator.data or {}).items()
        if not key.startswith("communication_")
        and key not in {"inverter_serial_number", "logger_mac_address"}
    }

    cloud_guard = await async_read_cloud_guard_capabilities(
        hass, str(entry.data[CONF_HOST])
    )

    return {
        "config_entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "device": {
            "model_family": coordinator.client.model,
            "protocol": coordinator.client.protocol_name,
            "pv_count": coordinator.client.pv_count,
            "pv_count_strategy": "progressive_highest_observed_input",
            "measurement_keys": sorted(coordinator.client.measurement_keys),
            "logger_firmware_version": firmware_version,
            "inverter_serial_prefix": coordinator.inverter_serial_prefix,
            "firmware_protocol_hint": firmware_protocol_hint,
            "firmware_protocol_matches_selected": (
                firmware_protocol_hint == coordinator.client.protocol_name
                if firmware_protocol_hint is not None
                else None
            ),
        },
        "communication": coordinator.diagnostic_summary,
        "measurements": measurements,
        "protocol_trace": list(coordinator.client.diagnostic_trace),
        "cloud_guard_research": {
            "remote_server_configurable": cloud_guard.remote_server_configurable,
            "dns_configurable": cloud_guard.dns_configurable,
            "logger_firmware_upload_available": (
                cloud_guard.logger_firmware_upload_available
            ),
            "inverter_firmware_upload_available": (
                cloud_guard.inverter_firmware_upload_available
            ),
            "configured_server_ports": list(
                cloud_guard.configured_server_ports
            ),
            "ssl_cloud_configured": cloud_guard.ssl_cloud_configured,
            "write_operations_performed": (
                cloud_guard.write_operations_performed
            ),
        },
        "privacy": {
            "network_address_included": False,
            "logger_number_included": False,
            "logger_mac_address_included": False,
            "inverter_serial_number_included": False,
            "inverter_serial_prefix_included": (
                coordinator.inverter_serial_prefix is not None
            ),
            "ap_envelope_included": False,
            "cloud_server_hostname_included": False,
            "dns_server_address_included": False,
        },
    }
