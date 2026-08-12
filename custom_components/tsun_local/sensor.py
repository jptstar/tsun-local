# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Sensors for TSUN Local."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TsunConfigEntry
from .const import CONF_LOGGER_SN, DOMAIN, MANUFACTURER
from .coordinator import TsunCoordinator


@dataclass(frozen=True, kw_only=True)
class TsunSensorDescription(SensorEntityDescription):
    """Describe a TSUN sensor."""

    suggested_object_id: str | None = None
    register_address: str | None = None


def _measurement(
    key: str,
    translation_key: str,
    device_class: SensorDeviceClass,
    unit: str,
    precision: int,
    state_class: SensorStateClass = SensorStateClass.MEASUREMENT,
) -> TsunSensorDescription:
    return TsunSensorDescription(
        key=key,
        suggested_object_id=key,
        translation_key=translation_key,
        device_class=device_class,
        native_unit_of_measurement=unit,
        state_class=state_class,
        suggested_display_precision=precision,
    )


def _raw_alarm(
    key: str, translation_key: str, register_address: str
) -> TsunSensorDescription:
    """Describe one read-only raw alarm register."""
    return TsunSensorDescription(
        key=key,
        suggested_object_id=key,
        translation_key=translation_key,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_address=register_address,
    )


COMMUNICATION_SENSOR_KEYS = frozenset(
    {
        "communication_last_success",
        "communication_duration",
        "communication_blocks",
        "communication_failures",
    }
)
LOGGER_METADATA_SENSOR_KEYS = frozenset(
    {"logger_firmware_version", "logger_mac_address"}
)
DIAGNOSTIC_SENSOR_KEYS = COMMUNICATION_SENSOR_KEYS | LOGGER_METADATA_SENSOR_KEYS


SENSORS: tuple[TsunSensorDescription, ...] = (
    _measurement(
        "ac_voltage",
        "ac_voltage",
        SensorDeviceClass.VOLTAGE,
        UnitOfElectricPotential.VOLT,
        1,
    ),
    _measurement(
        "ac_current",
        "ac_current",
        SensorDeviceClass.CURRENT,
        UnitOfElectricCurrent.AMPERE,
        2,
    ),
    _measurement(
        "ac_frequency",
        "ac_frequency",
        SensorDeviceClass.FREQUENCY,
        UnitOfFrequency.HERTZ,
        2,
    ),
    _measurement("ac_power", "ac_power", SensorDeviceClass.POWER, UnitOfPower.WATT, 1),
    _measurement(
        "ac_energy_today",
        "ac_energy_today",
        SensorDeviceClass.ENERGY,
        UnitOfEnergy.KILO_WATT_HOUR,
        2,
        SensorStateClass.TOTAL_INCREASING,
    ),
    _measurement(
        "ac_energy_total",
        "ac_energy_total",
        SensorDeviceClass.ENERGY,
        UnitOfEnergy.KILO_WATT_HOUR,
        2,
        SensorStateClass.TOTAL_INCREASING,
    ),
    _measurement(
        "dc_power_total",
        "dc_power_total",
        SensorDeviceClass.POWER,
        UnitOfPower.WATT,
        1,
    ),
    TsunSensorDescription(
        key="communication_last_success",
        suggested_object_id="communication_last_success",
        translation_key="communication_last_success",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TsunSensorDescription(
        key="communication_duration",
        suggested_object_id="communication_duration",
        translation_key="communication_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TsunSensorDescription(
        key="communication_blocks",
        suggested_object_id="communication_blocks",
        translation_key="communication_blocks",
        native_unit_of_measurement="blocks",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TsunSensorDescription(
        key="communication_failures",
        suggested_object_id="communication_failures",
        translation_key="communication_failures",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TsunSensorDescription(
        key="logger_firmware_version",
        suggested_object_id="logger_firmware_version",
        translation_key="logger_firmware_version",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TsunSensorDescription(
        key="logger_mac_address",
        suggested_object_id="logger_mac_address",
        translation_key="logger_mac_address",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    *(
        _raw_alarm(
            f"alarm_global_{index}_raw",
            f"alarm_global_{index}_raw",
            f"0x{0x0BBB + index:04X}",
        )
        for index in range(4)
    ),
    *(
        _raw_alarm(
            f"alarm_secondary_{index}_raw",
            f"alarm_secondary_{index}_raw",
            f"0x{0x0CE4 + index:04X}",
        )
        for index in range(4)
    ),
    *(
        _raw_alarm(
            f"alarm_code_{index}_raw",
            f"alarm_code_{index}_raw",
            f"0x{0x3002 + index:04X}",
        )
        for index in range(1, 5)
    ),
)

PV_ALARM_REGISTERS = (0x0E16, 0x0E1D, 0x0E24, 0x0EDE, 0x0EE5, 0x0EEC)

PV_SENSORS: tuple[TsunSensorDescription, ...] = tuple(
    description
    for number in range(1, 7)
    for description in (
        _measurement(
            f"pv{number}_voltage",
            f"pv{number}_voltage",
            SensorDeviceClass.VOLTAGE,
            UnitOfElectricPotential.VOLT,
            1,
        ),
        _measurement(
            f"pv{number}_current",
            f"pv{number}_current",
            SensorDeviceClass.CURRENT,
            UnitOfElectricCurrent.AMPERE,
            2,
        ),
        _measurement(
            f"pv{number}_power",
            f"pv{number}_power",
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            1,
        ),
        _measurement(
            f"pv{number}_energy_today",
            f"pv{number}_energy_today",
            SensorDeviceClass.ENERGY,
            UnitOfEnergy.KILO_WATT_HOUR,
            2,
            SensorStateClass.TOTAL_INCREASING,
        ),
        _measurement(
            f"pv{number}_energy_total",
            f"pv{number}_energy_total",
            SensorDeviceClass.ENERGY,
            UnitOfEnergy.KILO_WATT_HOUR,
            2,
            SensorStateClass.TOTAL_INCREASING,
        ),
        _raw_alarm(
            f"pv{number}_alarm_raw",
            f"pv{number}_alarm_raw",
            f"0x{PV_ALARM_REGISTERS[number - 1]:04X}",
        ),
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TsunConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors supported by this device protocol."""
    coordinator = entry.runtime_data
    added_keys: set[str] = set()

    @callback
    def async_add_discovered_entities() -> None:
        """Add sensors when protocol or PV-input discovery exposes new keys."""
        descriptions = [
            description
            for description in SENSORS + PV_SENSORS
            if description.key not in added_keys
            and (
                description.key in DIAGNOSTIC_SENSOR_KEYS
                or description.key in coordinator.client.measurement_keys
            )
        ]
        if not descriptions:
            return
        added_keys.update(description.key for description in descriptions)
        async_add_entities(
            TsunSensor(coordinator, entry, description)
            for description in descriptions
        )

    async_add_discovered_entities()
    entry.async_on_unload(
        coordinator.async_add_listener(async_add_discovered_entities)
    )


class TsunSensor(CoordinatorEntity[TsunCoordinator], SensorEntity):
    """A sensor belonging to one locally connected TSUN device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: TsunCoordinator,
        entry: TsunConfigEntry,
        description: TsunSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        logger_sn = str(entry.data[CONF_LOGGER_SN])
        self._attr_unique_id = f"{logger_sn}_{description.key}"
        firmware_version = coordinator.data.get("logger_firmware_version")
        mac_address = coordinator.data.get("logger_mac_address")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, logger_sn)},
            manufacturer=MANUFACTURER,
            model=coordinator.client.model,
            name=f"TSUN Local {logger_sn}",
            serial_number=logger_sn,
            sw_version=(
                str(firmware_version)
                if firmware_version is not None
                else None
            ),
            connections=(
                {(CONNECTION_NETWORK_MAC, str(mac_address))}
                if mac_address is not None
                else set()
            ),
        )

    @property
    @override
    def suggested_object_id(self) -> str | None:
        """Return a stable English identifier independent of the UI language."""
        return self.entity_description.suggested_object_id

    @property
    def native_value(self) -> Any:
        """Return the latest decoded value."""
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Expose the source address and hexadecimal value for raw alarms."""
        address = self.entity_description.register_address
        value = self.native_value
        if address is None or not isinstance(value, int):
            return None
        return {
            "register_address": address,
            "raw_value_hex": f"0x{value:04X}",
        }

    @property
    def available(self) -> bool:
        """Keep diagnostics and energy counters available while offline."""
        key = self.entity_description.key
        if self.entity_description.register_address is not None:
            return (
                super().available
                and bool(self.coordinator.data.get("communication_online", False))
                and key in self.coordinator.data
            )
        if (
            key in DIAGNOSTIC_SENSOR_KEYS
            or self.entity_description.device_class == SensorDeviceClass.ENERGY
        ):
            return super().available
        return super().available and bool(
            self.coordinator.data.get("communication_online", False)
        )
