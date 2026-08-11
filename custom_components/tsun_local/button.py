# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Manual refresh button for TSUN Local."""

from __future__ import annotations

from typing import override

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TsunConfigEntry
from .const import CONF_LOGGER_SN, DOMAIN, MANUFACTURER
from .coordinator import TsunCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TsunConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the manual data-refresh button."""
    async_add_entities([TsunRefreshButton(entry.runtime_data, entry)])


class TsunRefreshButton(CoordinatorEntity[TsunCoordinator], ButtonEntity):
    """Trigger one immediate complete poll of this micro-inverter."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:refresh"
    _attr_translation_key = "refresh_data"

    def __init__(self, coordinator: TsunCoordinator, entry: TsunConfigEntry) -> None:
        super().__init__(coordinator)
        logger_sn = str(entry.data[CONF_LOGGER_SN])
        self._attr_unique_id = f"{logger_sn}_refresh_data"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, logger_sn)},
            manufacturer=MANUFACTURER,
            model=coordinator.client.model,
            name=f"TSUN Local {logger_sn}",
            serial_number=logger_sn,
        )

    @property
    @override
    def suggested_object_id(self) -> str:
        """Return a stable English identifier independent of the UI language."""
        return "refresh_data"

    async def async_press(self) -> None:
        """Run an immediate poll and update every entity of this device."""
        await self.coordinator.async_refresh()
