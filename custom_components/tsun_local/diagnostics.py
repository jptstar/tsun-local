# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Privacy-safe diagnostics support for TSUN Local."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from . import TsunConfigEntry
from .const import CONF_LOGGER_SN

TO_REDACT = {CONF_HOST, CONF_LOGGER_SN}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: TsunConfigEntry
) -> dict[str, Any]:
    """Return diagnostics with the network address and logger number redacted."""
    coordinator = entry.runtime_data
    measurements = {
        key: value
        for key, value in (coordinator.data or {}).items()
        if not key.startswith("communication_")
    }
    return {
        "config_entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "device": {
            "model_family": coordinator.client.model,
            "protocol": coordinator.client.protocol_name,
            "pv_count": coordinator.client.pv_count,
            "measurement_keys": sorted(coordinator.client.measurement_keys),
        },
        "communication": coordinator.diagnostic_summary,
        "measurements": measurements,
        "protocol_trace": list(coordinator.client.diagnostic_trace),
        "privacy": {
            "network_address_included": False,
            "logger_number_included": False,
            "ap_envelope_included": False,
        },
    }
