# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Binary sensors for TSUN Local."""

from __future__ import annotations

from typing import override

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
from .const import CONF_LOGGER_SN, DOMAIN, MANUFACTURER
from .coordinator import TsunCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TsunConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up communication and inverter-alarm status sensors."""
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = [
        TsunConnectivitySensor(coordinator, entry)
    ]
    if "alarm_active" in coordinator.client.measurement_keys:
        entities.append(TsunAlarmSensor(coordinator, entry))
    async_add_entities(entities)


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
            model=coordinator.client.model,
            name=f"TSUN Local {logger_sn}",
            serial_number=logger_sn,
        )

    @property
    @override
    def suggested_object_id(self) -> str:
        """Return a stable English identifier independent of the UI language."""
        return "communication_online"

    @property
    def is_on(self) -> bool:
        """Return true when the logger answered the latest poll."""
        return bool(self.coordinator.data.get("communication_online", False))


class TsunAlarmSensor(CoordinatorEntity[TsunCoordinator], BinarySensorEntity):
    """Report whether any protocol alarm register is non-zero."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True
    _attr_translation_key = "inverter_alarm"

    def __init__(self, coordinator: TsunCoordinator, entry: TsunConfigEntry) -> None:
        super().__init__(coordinator)
        logger_sn = str(entry.data[CONF_LOGGER_SN])
        self._attr_unique_id = f"{logger_sn}_inverter_alarm"
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
        return "inverter_alarm"

    @property
    def is_on(self) -> bool:
        """Return true when at least one complete alarm word is non-zero."""
        return bool(self.coordinator.data.get("alarm_active", False))

    @property
    def available(self) -> bool:
        """Do not present stale alarm state while the device is offline."""
        return (
            super().available
            and bool(self.coordinator.data.get("communication_online", False))
            and "alarm_active" in self.coordinator.data
        )

    @property
    def extra_state_attributes(self) -> dict[str, dict[str, int]]:
        """List only non-zero raw alarm values for diagnostics."""
        active_values = {
            key: value
            for key, value in self.coordinator.data.items()
            if (
                isinstance(value, int)
                and value != 0
                and (
                    key.startswith("alarm_") and key.endswith("_raw")
                    or key.startswith("pv") and key.endswith("_alarm_raw")
                )
            )
        }
        return {"active_raw_values": active_values}
