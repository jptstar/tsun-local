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
    CONF_UNIT_OF_MEASUREMENT,
    EntityCategory,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import DeviceInfo
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


def _raw_register(
    key: str,
    translation_key: str,
    register_address: str,
    *,
    chartable: bool = False,
) -> TsunSensorDescription:
    """Describe one read-only raw diagnostic register."""
    return TsunSensorDescription(
        key=key,
        suggested_object_id=key,
        translation_key=translation_key,
        state_class=SensorStateClass.MEASUREMENT if chartable else None,
        suggested_display_precision=0 if chartable else None,
        entity_category=EntityCategory.DIAGNOSTIC,
        register_address=register_address,
    )


def _diagnostic_power(key: str, translation_key: str) -> TsunSensorDescription:
    """Describe one read-only power rating diagnostic."""
    return TsunSensorDescription(
        key=key,
        suggested_object_id=key,
        translation_key=translation_key,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
    )


def _advanced_diagnostic(
    key: str,
    translation_key: str,
    *,
    device_class: SensorDeviceClass | None = None,
    unit: str | None = None,
    precision: int | None = None,
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT,
) -> TsunSensorDescription:
    """Describe an advanced read-only diagnostic disabled by default."""
    return TsunSensorDescription(
        key=key,
        suggested_object_id=key,
        translation_key=translation_key,
        device_class=device_class,
        native_unit_of_measurement=unit,
        state_class=state_class,
        suggested_display_precision=precision,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
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
    {
        "label_serial_number",
        "inverter_serial_number",
        "logger_firmware_version",
        "logger_mac_address",
        "logger_wifi_signal",
    }
)
DIAGNOSTIC_SENSOR_KEYS = COMMUNICATION_SENSOR_KEYS | LOGGER_METADATA_SENSOR_KEYS

GRID_TIMING_SENSOR_KEYS = frozenset(
    {
        "grid_undervoltage_time_1",
        "grid_undervoltage_time_2",
        "grid_undervoltage_time_3",
        "grid_overvoltage_time_1",
        "grid_overvoltage_time_2",
        "grid_underfrequency_time_1",
        "grid_underfrequency_time_2",
        "grid_overfrequency_time_1",
        "grid_overfrequency_time_2",
    }
)

PROTOCOL_REGISTER_ADDRESSES: dict[str, dict[str, str]] = {
    "1511": {
        "inverter_status_raw": "3000 (0x0BB8)",
        "rated_power": "3020 (0x0BCC)",
        "max_designed_power": "2042 (0x07FA)",
        "grid_overvoltage_recovery_voltage": "0x07D4",
        "grid_undervoltage_recovery_voltage": "0x07D5",
        "grid_overfrequency_recovery_frequency": "0x07D6",
        "grid_underfrequency_recovery_frequency": "0x07D7",
        "grid_undervoltage_level_1": "0x07D9",
        "grid_undervoltage_level_2": "0x07DA",
        "grid_undervoltage_time_1": "0x07DB",
        "grid_undervoltage_time_2": "0x07DC",
        "grid_overvoltage_level_1": "0x07DD",
        "grid_overvoltage_level_2": "0x07DE",
        "grid_overvoltage_time_1": "0x07DF",
        "grid_overvoltage_time_2": "0x07E0",
        "grid_underfrequency_level_1": "0x07E2",
        "grid_underfrequency_level_2": "0x07E3",
        "grid_underfrequency_time_1": "0x07E4",
        "grid_underfrequency_time_2": "0x07E5",
        "grid_overfrequency_level_1": "0x07E6",
        "grid_overfrequency_level_2": "0x07E7",
        "grid_overfrequency_time_1": "0x07E8",
        "grid_overfrequency_time_2": "0x07E9",
        "grid_undervoltage_level_3": "0x07EA",
        "grid_undervoltage_time_3": "0x07EB",
        "output_coefficient_candidate": "2028 (0x07EC) — candidate",
    },
    "02b0": {
        "inverter_status_raw": "0x3000",
        "rated_power": "0x300E",
        "max_designed_power": "0x2007",
        "grid_overvoltage_recovery_voltage": "0x2014",
        "grid_undervoltage_recovery_voltage": "0x2015",
        "grid_overfrequency_recovery_frequency": "0x2016",
        "grid_underfrequency_recovery_frequency": "0x2017",
        "grid_undervoltage_level_1": "0x2019",
        "grid_undervoltage_level_2": "0x201A",
        "grid_undervoltage_time_1": "0x201B",
        "grid_undervoltage_time_2": "0x201C",
        "grid_overvoltage_level_1": "0x201D",
        "grid_overvoltage_level_2": "0x201E",
        "grid_overvoltage_time_1": "0x201F",
        "grid_overvoltage_time_2": "0x2020",
        "grid_underfrequency_level_1": "0x2022",
        "grid_underfrequency_level_2": "0x2023",
        "grid_underfrequency_time_1": "0x2024",
        "grid_underfrequency_time_2": "0x2025",
        "grid_overfrequency_level_1": "0x2026",
        "grid_overfrequency_level_2": "0x2027",
        "grid_overfrequency_time_1": "0x2028",
        "grid_overfrequency_time_2": "0x2029",
        "grid_undervoltage_level_3": "0x202A",
        "grid_undervoltage_time_3": "0x202B",
        "output_coefficient": "0x202C",
    },
    "1097": {
        "inverter_status_raw": "0x1100",
        "rated_power": "0x1210",
        "max_designed_power": "0x1437",
        "protocol_version": "0x100A",
        "inverter_version": "0x100C",
        "insulation_impedance_rx": "0x1216",
        "insulation_impedance_ry": "0x1217",
        "inverter_temperature": "0x1218",
        "country_profile_raw": "0x1400",
        "output_coefficient": "0x1423 — experimental",
    },
}


ADVANCED_DIAGNOSTIC_SENSORS: tuple[TsunSensorDescription, ...] = (
    _advanced_diagnostic(
        "grid_overvoltage_recovery_voltage",
        "grid_overvoltage_recovery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _advanced_diagnostic(
        "grid_undervoltage_recovery_voltage",
        "grid_undervoltage_recovery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _advanced_diagnostic(
        "grid_overfrequency_recovery_frequency",
        "grid_overfrequency_recovery_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        unit=UnitOfFrequency.HERTZ,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_underfrequency_recovery_frequency",
        "grid_underfrequency_recovery_frequency",
        device_class=SensorDeviceClass.FREQUENCY,
        unit=UnitOfFrequency.HERTZ,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_undervoltage_level_1",
        "grid_undervoltage_level_1",
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _advanced_diagnostic(
        "grid_undervoltage_level_2",
        "grid_undervoltage_level_2",
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _advanced_diagnostic(
        "grid_undervoltage_time_1",
        "grid_undervoltage_time_1",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_undervoltage_time_2",
        "grid_undervoltage_time_2",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_overvoltage_level_1",
        "grid_overvoltage_level_1",
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _advanced_diagnostic(
        "grid_overvoltage_level_2",
        "grid_overvoltage_level_2",
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _advanced_diagnostic(
        "grid_overvoltage_time_1",
        "grid_overvoltage_time_1",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_overvoltage_time_2",
        "grid_overvoltage_time_2",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_underfrequency_level_1",
        "grid_underfrequency_level_1",
        device_class=SensorDeviceClass.FREQUENCY,
        unit=UnitOfFrequency.HERTZ,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_underfrequency_level_2",
        "grid_underfrequency_level_2",
        device_class=SensorDeviceClass.FREQUENCY,
        unit=UnitOfFrequency.HERTZ,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_underfrequency_time_1",
        "grid_underfrequency_time_1",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_underfrequency_time_2",
        "grid_underfrequency_time_2",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_overfrequency_level_1",
        "grid_overfrequency_level_1",
        device_class=SensorDeviceClass.FREQUENCY,
        unit=UnitOfFrequency.HERTZ,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_overfrequency_level_2",
        "grid_overfrequency_level_2",
        device_class=SensorDeviceClass.FREQUENCY,
        unit=UnitOfFrequency.HERTZ,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_overfrequency_time_1",
        "grid_overfrequency_time_1",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_overfrequency_time_2",
        "grid_overfrequency_time_2",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "grid_undervoltage_level_3",
        "grid_undervoltage_level_3",
        device_class=SensorDeviceClass.VOLTAGE,
        unit=UnitOfElectricPotential.VOLT,
        precision=1,
    ),
    _advanced_diagnostic(
        "grid_undervoltage_time_3",
        "grid_undervoltage_time_3",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        precision=2,
    ),
    _advanced_diagnostic(
        "output_coefficient",
        "output_coefficient",
        unit=PERCENTAGE,
        precision=1,
    ),
    _advanced_diagnostic(
        "output_coefficient_candidate",
        "output_coefficient_candidate",
        unit=PERCENTAGE,
        precision=1,
    ),
    _advanced_diagnostic(
        "protocol_version",
        "protocol_version",
        state_class=None,
    ),
    _advanced_diagnostic(
        "inverter_version",
        "inverter_version",
        state_class=None,
    ),
    _advanced_diagnostic(
        "insulation_impedance_rx",
        "insulation_impedance_rx",
        unit="MΩ",
        precision=2,
    ),
    _advanced_diagnostic(
        "insulation_impedance_ry",
        "insulation_impedance_ry",
        unit="MΩ",
        precision=2,
    ),
    _advanced_diagnostic(
        "inverter_temperature",
        "inverter_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        precision=0,
    ),
    _advanced_diagnostic(
        "ambient_temperature",
        "ambient_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        unit=UnitOfTemperature.CELSIUS,
        precision=0,
    ),
    _advanced_diagnostic(
        "country_profile_raw",
        "country_profile_raw",
        state_class=None,
    ),
)

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
    _raw_register(
        "inverter_status_raw",
        "inverter_status_raw",
        "3000 (0x0BB8)",
    ),
    TsunSensorDescription(
        key="inverter_operating_state",
        suggested_object_id="inverter_operating_state",
        translation_key="inverter_operating_state",
        device_class=SensorDeviceClass.ENUM,
        options=["active", "standby", "standby_low_solar", "fault"],
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    _raw_register(
        "register_3017_raw",
        "register_3017_raw",
        "3017 (0x0BC9)",
        chartable=True,
    ),
    _raw_register(
        "register_3018_raw",
        "register_3018_raw",
        "3018 (0x0BCA)",
    ),
    _raw_register(
        "register_3028_raw",
        "register_3028_raw",
        "3028 (0x0BD4)",
        chartable=True,
    ),
    _diagnostic_power("rated_power", "rated_power"),
    _diagnostic_power("max_designed_power", "max_designed_power"),
    *ADVANCED_DIAGNOSTIC_SENSORS,
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
        key="label_serial_number",
        suggested_object_id="label_serial_number",
        translation_key="label_serial_number",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TsunSensorDescription(
        key="inverter_serial_number",
        suggested_object_id="inverter_serial_number",
        translation_key="inverter_serial_number",
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
    TsunSensorDescription(
        key="logger_wifi_signal",
        suggested_object_id="logger_wifi_signal",
        translation_key="logger_wifi_signal",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
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


@callback
def _migrate_legacy_sensor_units(
    hass: HomeAssistant, entry: TsunConfigEntry
) -> None:
    """Migrate automatic beta-era display units without overriding user choices."""
    registry = er.async_get(hass)
    logger_sn = str(entry.data[CONF_LOGGER_SN])

    def _registry_entry(key: str) -> er.RegistryEntry | None:
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{logger_sn}_{key}"
        )
        return registry.async_get(entity_id) if entity_id is not None else None

    for key in GRID_TIMING_SENSOR_KEYS:
        registry_entry = _registry_entry(key)
        if registry_entry is None:
            continue
        sensor_options = registry_entry.options.get("sensor", {})
        if CONF_UNIT_OF_MEASUREMENT in sensor_options:
            continue

        if registry_entry.unit_of_measurement == UnitOfTime.MILLISECONDS:
            registry_entry = registry.async_update_entity(
                registry_entry.entity_id,
                unit_of_measurement=UnitOfTime.SECONDS,
            )

        private_options = registry_entry.options.get("sensor.private", {})
        if (
            private_options.get("suggested_unit_of_measurement")
            == UnitOfTime.MILLISECONDS
        ):
            registry.async_update_entity_options(
                registry_entry.entity_id, "sensor.private", None
            )

    output_entry = _registry_entry("output_coefficient")
    if output_entry is None:
        return
    sensor_options = output_entry.options.get("sensor", {})
    if CONF_UNIT_OF_MEASUREMENT in sensor_options:
        return

    if output_entry.unit_of_measurement == PERCENTAGE:
        output_entry = registry.async_update_entity(
            output_entry.entity_id,
            unit_of_measurement=None,
        )

    private_options = output_entry.options.get("sensor.private", {})
    if private_options.get("suggested_unit_of_measurement") == PERCENTAGE:
        registry.async_update_entity_options(
            output_entry.entity_id, "sensor.private", None
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TsunConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors supported by this device protocol."""
    _migrate_legacy_sensor_units(hass, entry)
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
        self._label_serial_number = logger_sn
        self._attr_unique_id = f"{logger_sn}_{description.key}"
        firmware_version = coordinator.data.get("logger_firmware_version")
        inverter_serial_number = coordinator.data.get("inverter_serial_number")
        raw_profile = coordinator.data.get("logger_raw_profile")
        self._attr_device_info = DeviceInfo(
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
                str(firmware_version)
                if firmware_version is not None
                else None
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
        if self.entity_description.key == "label_serial_number":
            return self._label_serial_number
        return self.coordinator.data.get(self.entity_description.key)

    def _source_register_address(self) -> str | None:
        """Return the register address used by the active protocol."""
        protocol_name = str(getattr(self.coordinator.client, "protocol_name", ""))
        return PROTOCOL_REGISTER_ADDRESSES.get(protocol_name, {}).get(
            self.entity_description.key, self.entity_description.register_address
        )

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Expose the source address and hexadecimal value for raw registers."""
        address = self._source_register_address()
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
        if self._source_register_address() is not None:
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
