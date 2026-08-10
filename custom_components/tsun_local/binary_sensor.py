# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Binary sensors for TSUN Local devices using protocol 1511."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TsunConfigEntry
from .const import CONF_LOGGER_SN, DOMAIN, MANUFACTURER, MODEL
from .coordinator import TsunCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TsunConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the communication status sensor."""
    async_add_entities([TsunConnectivitySensor(entry.runtime_data, entry)])


class TsunConnectivitySensor(
    CoordinatorEntity[TsunCoordinator], BinarySensorEntity
):
    """Report whether the local logger is reachable."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "communication_online"

    def __init__(self, coordinator: TsunCoordinator, entry: TsunConfigEntry) -> None:
        super().__init__(coordinator)
        logger_sn = str(entry.data[CONF_LOGGER_SN])
        self._attr_unique_id = f"{logger_sn}_communication_online"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, logger_sn)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=f"TSUN Local {logger_sn}",
            serial_number=logger_sn,
        )

    @property
    def is_on(self) -> bool:
        """Return true when the logger answered the latest poll."""
        return bool(self.coordinator.data.get("communication_online", False))
