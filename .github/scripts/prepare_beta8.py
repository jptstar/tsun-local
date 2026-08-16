from __future__ import annotations

import json
import re
from pathlib import Path

VERSION = "1.4.0-beta.8"
ROOT = Path(".")

GRID_KEYS = (
    "grid_overvoltage_recovery_voltage",
    "grid_undervoltage_recovery_voltage",
    "grid_overfrequency_recovery_frequency",
    "grid_underfrequency_recovery_frequency",
    "grid_undervoltage_level_1",
    "grid_undervoltage_level_2",
    "grid_undervoltage_time_1",
    "grid_undervoltage_time_2",
    "grid_overvoltage_level_1",
    "grid_overvoltage_level_2",
    "grid_overvoltage_time_1",
    "grid_overvoltage_time_2",
    "grid_underfrequency_level_1",
    "grid_underfrequency_level_2",
    "grid_underfrequency_time_1",
    "grid_underfrequency_time_2",
    "grid_overfrequency_level_1",
    "grid_overfrequency_level_2",
    "grid_overfrequency_time_1",
    "grid_overfrequency_time_2",
    "grid_undervoltage_level_3",
    "grid_undervoltage_time_3",
)

GRID_1511 = {
    "grid_overvoltage_recovery_voltage": (0x07D4, 0.1),
    "grid_undervoltage_recovery_voltage": (0x07D5, 0.1),
    "grid_overfrequency_recovery_frequency": (0x07D6, 0.01),
    "grid_underfrequency_recovery_frequency": (0x07D7, 0.01),
    "grid_undervoltage_level_1": (0x07D9, 0.1),
    "grid_undervoltage_level_2": (0x07DA, 0.1),
    "grid_undervoltage_time_1": (0x07DB, 0.02),
    "grid_undervoltage_time_2": (0x07DC, 0.02),
    "grid_overvoltage_level_1": (0x07DD, 0.1),
    "grid_overvoltage_level_2": (0x07DE, 0.1),
    "grid_overvoltage_time_1": (0x07DF, 0.02),
    "grid_overvoltage_time_2": (0x07E0, 0.02),
    "grid_underfrequency_level_1": (0x07E2, 0.01),
    "grid_underfrequency_level_2": (0x07E3, 0.01),
    "grid_underfrequency_time_1": (0x07E4, 0.02),
    "grid_underfrequency_time_2": (0x07E5, 0.02),
    "grid_overfrequency_level_1": (0x07E6, 0.01),
    "grid_overfrequency_level_2": (0x07E7, 0.01),
    "grid_overfrequency_time_1": (0x07E8, 0.02),
    "grid_overfrequency_time_2": (0x07E9, 0.02),
    "grid_undervoltage_level_3": (0x07EA, 0.1),
    "grid_undervoltage_time_3": (0x07EB, 0.02),
}

GRID_02B0 = {
    "grid_overvoltage_recovery_voltage": (0x2014, 0.1),
    "grid_undervoltage_recovery_voltage": (0x2015, 0.1),
    "grid_overfrequency_recovery_frequency": (0x2016, 0.01),
    "grid_underfrequency_recovery_frequency": (0x2017, 0.01),
    "grid_undervoltage_level_1": (0x2019, 0.1),
    "grid_undervoltage_level_2": (0x201A, 0.1),
    "grid_undervoltage_time_1": (0x201B, 0.02),
    "grid_undervoltage_time_2": (0x201C, 0.02),
    "grid_overvoltage_level_1": (0x201D, 0.1),
    "grid_overvoltage_level_2": (0x201E, 0.1),
    "grid_overvoltage_time_1": (0x201F, 0.02),
    "grid_overvoltage_time_2": (0x2020, 0.02),
    "grid_underfrequency_level_1": (0x2022, 0.01),
    "grid_underfrequency_level_2": (0x2023, 0.01),
    "grid_underfrequency_time_1": (0x2024, 0.02),
    "grid_underfrequency_time_2": (0x2025, 0.02),
    "grid_overfrequency_level_1": (0x2026, 0.01),
    "grid_overfrequency_level_2": (0x2027, 0.01),
    "grid_overfrequency_time_1": (0x2028, 0.02),
    "grid_overfrequency_time_2": (0x2029, 0.02),
    "grid_undervoltage_level_3": (0x202A, 0.1),
    "grid_undervoltage_time_3": (0x202B, 0.02),
    "output_coefficient": (0x202C, 1.0),
}


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    text = read(path)
    if old not in text:
        raise RuntimeError(f"Expected text not found in {path}: {old[:100]!r}")
    write(path, text.replace(old, new, 1))


def insert_before(path: str, marker: str, addition: str) -> None:
    text = read(path)
    if marker not in text:
        raise RuntimeError(f"Marker not found in {path}: {marker[:100]!r}")
    write(path, text.replace(marker, addition + marker, 1))


# 1511: correct PV daily-energy positions and decode the known read-only grid map.
p1511 = "custom_components/tsun_local/protocols/protocol_1511.py"
replace_once(
    p1511,
    "addresses = (base, base + 1, base + 2, base + 4, total_pair, total_pair + 1)",
    "addresses = (base, base + 1, base + 2, base + 5, total_pair, total_pair + 1)",
)
replace_once(
    p1511,
    'data[f"{prefix}_energy_today"] = registers[base + 4] * 0.01',
    'data[f"{prefix}_energy_today"] = registers[base + 5] * 0.01',
)
insert_before(
    p1511,
    "PV_MEASUREMENT_NAMES = (\n",
    "ADVANCED_GRID_KEYS = frozenset(\n"
    "    {\n"
    + "".join(f'        "{key}",\n' for key in GRID_KEYS)
    + "    }\n)\n\n"
    "ADVANCED_GRID_REGISTERS: dict[str, tuple[int, float]] = {\n"
    + "".join(
        f'    "{key}": (0x{address:04X}, {factor}),\n'
        for key, (address, factor) in GRID_1511.items()
    )
    + "}\n\n\n",
)
replace_once(
    p1511,
    "        | TITAN_DIAGNOSTIC_KEYS\n        | ALARM_MEASUREMENT_KEYS",
    "        | TITAN_DIAGNOSTIC_KEYS\n        | ADVANCED_GRID_KEYS\n        | ALARM_MEASUREMENT_KEYS",
)
insert_before(
    p1511,
    "def decode_alarms(\n",
    "def decode_advanced_diagnostics(registers: dict[int, int]) -> dict[str, float]:\n"
    "    \"\"\"Decode read-only grid protection diagnostics.\"\"\"\n"
    "    return {\n"
    "        key: round(registers[address] * factor, 2)\n"
    "        for key, (address, factor) in ADVANCED_GRID_REGISTERS.items()\n"
    "        if address in registers\n"
    "    }\n\n\n",
)
replace_once(
    p1511,
    "        measurements = decode_measurements(registers, self._pv_count)\n        measurements.update(decode_alarms(registers, self._pv_count))",
    "        measurements = decode_measurements(registers, self._pv_count)\n        measurements.update(decode_advanced_diagnostics(registers))\n        measurements.update(decode_alarms(registers, self._pv_count))",
)

# 02B0: read/decode the full advanced grid block and read the output coefficient.
p02 = "custom_components/tsun_local/protocols/protocol_02b0.py"
replace_once(
    p02,
    "DIAGNOSTIC_BLOCKS = (\n    # Public TSUN community mapping: maximum designed power.\n    (0x03, 0x2007, 0x2007),\n)",
    "DIAGNOSTIC_BLOCKS = (\n    (0x03, 0x2007, 0x2007),\n    # Advanced read-only grid parameters and output coefficient.\n    (0x03, 0x2014, 0x202C),\n)",
)
insert_before(
    p02,
    "PV_MEASUREMENT_NAMES = (\n",
    "ADVANCED_GRID_KEYS = frozenset(\n"
    "    {\n"
    + "".join(f'        "{key}",\n' for key in (*GRID_KEYS, "output_coefficient"))
    + "    }\n)\n\n"
    "ADVANCED_GRID_REGISTERS: dict[str, tuple[int, float]] = {\n"
    + "".join(
        f'    "{key}": (0x{address:04X}, {factor}),\n'
        for key, (address, factor) in GRID_02B0.items()
    )
    + "}\n\n\n",
)
replace_once(
    p02,
    "        AC_MEASUREMENT_KEYS\n        | DEVICE_DIAGNOSTIC_KEYS\n        | ALARM_MEASUREMENT_KEYS",
    "        AC_MEASUREMENT_KEYS\n        | DEVICE_DIAGNOSTIC_KEYS\n        | ADVANCED_GRID_KEYS\n        | ALARM_MEASUREMENT_KEYS",
)
insert_before(
    p02,
    "def decode_alarms(registers: dict[int, int]) -> dict[str, float | int]:\n",
    "def decode_advanced_diagnostics(registers: dict[int, int]) -> dict[str, float]:\n"
    "    \"\"\"Decode read-only grid protection diagnostics.\"\"\"\n"
    "    return {\n"
    "        key: round(registers[address] * factor, 2)\n"
    "        for key, (address, factor) in ADVANCED_GRID_REGISTERS.items()\n"
    "        if address in registers\n"
    "    }\n\n\n",
)
replace_once(
    p02,
    "        measurements = decode_measurements(registers, self._pv_count)\n        measurements.update(decode_alarms(registers))",
    "        measurements = decode_measurements(registers, self._pv_count)\n        measurements.update(decode_advanced_diagnostics(registers))\n        measurements.update(decode_alarms(registers))",
)

# 1097: add the documented experimental diagnostics from public protocol research.
p1097 = "custom_components/tsun_local/protocols/protocol_1097.py"
replace_once(
    p1097,
    "DIAGNOSTIC_BLOCKS = (\n    # Public 1097 mapping: maximum designed power.\n    (0x03, 0x1437, 0x1437),\n)",
    "DIAGNOSTIC_BLOCKS = (\n    # Public 1097 mapping: country/profile code and maximum designed power.\n    (0x03, 0x1400, 0x1400),\n    (0x03, 0x1437, 0x1437),\n)",
)
insert_before(
    p1097,
    "PV_MEASUREMENT_NAMES = (\n",
    "ADVANCED_DIAGNOSTIC_KEYS = frozenset(\n"
    "    {\n"
    "        \"protocol_version\",\n"
    "        \"inverter_version\",\n"
    "        \"insulation_impedance_rx\",\n"
    "        \"insulation_impedance_ry\",\n"
    "        \"inverter_temperature\",\n"
    "        \"country_profile_raw\",\n"
    "    }\n)\n\n\n",
)
replace_once(
    p1097,
    "        AC_MEASUREMENT_KEYS\n        | DEVICE_DIAGNOSTIC_KEYS\n        | ALARM_MEASUREMENT_KEYS",
    "        AC_MEASUREMENT_KEYS\n        | DEVICE_DIAGNOSTIC_KEYS\n        | ADVANCED_DIAGNOSTIC_KEYS\n        | ALARM_MEASUREMENT_KEYS",
)
insert_before(
    p1097,
    "def decode_measurements(\n",
    "def _decode_version(value: int) -> str:\n"
    "    \"\"\"Decode the packed inverter version format.\"\"\"\n"
    "    return (\n"
    "        f\"V{value >> 12}.{(value >> 8) & 0xF}.\"\n"
    "        f\"{(value >> 4) & 0xF}{value & 0xF:X}\"\n"
    "    )\n\n\n"
    "def decode_advanced_diagnostics(\n"
    "    registers: dict[int, int],\n"
    ") -> dict[str, float | int | str]:\n"
    "    \"\"\"Decode known experimental 1097 diagnostics.\"\"\"\n"
    "    data: dict[str, float | int | str] = {}\n"
    "    if 0x100A in registers:\n"
    "        data[\"protocol_version\"] = _decode_version(registers[0x100A])\n"
    "    if 0x100C in registers:\n"
    "        data[\"inverter_version\"] = _decode_version(registers[0x100C])\n"
    "    if 0x1216 in registers:\n"
    "        data[\"insulation_impedance_rx\"] = round(registers[0x1216] * 0.01, 2)\n"
    "    if 0x1217 in registers:\n"
    "        data[\"insulation_impedance_ry\"] = round(registers[0x1217] * 0.01, 2)\n"
    "    if 0x1218 in registers:\n"
    "        data[\"inverter_temperature\"] = registers[0x1218] - 40\n"
    "    if 0x1400 in registers:\n"
    "        data[\"country_profile_raw\"] = registers[0x1400]\n"
    "    return data\n\n\n",
)
replace_once(
    p1097,
    "        measurements = decode_measurements(registers, self._pv_count)\n        measurements.update(decode_alarms(registers))",
    "        measurements = decode_measurements(registers, self._pv_count)\n        measurements.update(decode_advanced_diagnostics(registers))\n        measurements.update(decode_alarms(registers))",
)

# Home Assistant sensor descriptions. Advanced values are disabled by default.
psensor = "custom_components/tsun_local/sensor.py"
replace_once(
    psensor,
    "    UnitOfPower,\n    UnitOfTime,\n)",
    "    UnitOfPower,\n    UnitOfTemperature,\n    UnitOfTime,\n)",
)
insert_before(
    psensor,
    "COMMUNICATION_SENSOR_KEYS = frozenset(\n",
    "def _advanced_diagnostic(\n"
    "    key: str,\n"
    "    translation_key: str,\n"
    "    *,\n"
    "    device_class: SensorDeviceClass | None = None,\n"
    "    unit: str | None = None,\n"
    "    precision: int | None = None,\n"
    "    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT,\n"
    ") -> TsunSensorDescription:\n"
    "    \"\"\"Describe an advanced read-only diagnostic disabled by default.\"\"\"\n"
    "    return TsunSensorDescription(\n"
    "        key=key,\n"
    "        suggested_object_id=key,\n"
    "        translation_key=translation_key,\n"
    "        device_class=device_class,\n"
    "        native_unit_of_measurement=unit,\n"
    "        state_class=state_class,\n"
    "        suggested_display_precision=precision,\n"
    "        entity_category=EntityCategory.DIAGNOSTIC,\n"
    "        entity_registry_enabled_default=False,\n"
    "    )\n\n\n",
)

protocol_addresses = {
    "1511": {
        "inverter_status_raw": "3000 (0x0BB8)",
        "rated_power": "3020 (0x0BCC)",
        "max_designed_power": "2042 (0x07FA)",
        **{key: f"0x{addr:04X}" for key, (addr, _) in GRID_1511.items()},
    },
    "02b0": {
        "inverter_status_raw": "0x3000",
        "rated_power": "0x300E",
        "max_designed_power": "0x2007",
        **{key: f"0x{addr:04X}" for key, (addr, _) in GRID_02B0.items()},
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
    },
}
text = read(psensor)
pattern = re.compile(
    r"PROTOCOL_REGISTER_ADDRESSES: dict\[str, dict\[str, str\]\] = \{.*?\n\}\n\n\nSENSORS:",
    re.S,
)
lines = ["PROTOCOL_REGISTER_ADDRESSES: dict[str, dict[str, str]] = {"]
for protocol, mapping in protocol_addresses.items():
    lines.append(f'    "{protocol}": {{')
    lines.extend(f'        "{key}": "{address}",' for key, address in mapping.items())
    lines.append("    },")
lines.extend(["}", "", "", "SENSORS:"])
text, count = pattern.subn("\n".join(lines), text, count=1)
if count != 1:
    raise RuntimeError("Could not replace protocol register address map")
write(psensor, text)

advanced_specs: list[tuple[str, str | None, str | None, int | None, bool]] = []
for key in GRID_KEYS:
    if "voltage" in key:
        advanced_specs.append((key, "SensorDeviceClass.VOLTAGE", "UnitOfElectricPotential.VOLT", 1, True))
    elif "frequency" in key:
        advanced_specs.append((key, "SensorDeviceClass.FREQUENCY", "UnitOfFrequency.HERTZ", 2, True))
    else:
        advanced_specs.append((key, "SensorDeviceClass.DURATION", "UnitOfTime.MILLISECONDS", 2, True))
advanced_specs.extend(
    [
        ("output_coefficient", None, "PERCENTAGE", 0, True),
        ("protocol_version", None, None, None, False),
        ("inverter_version", None, None, None, False),
        ("insulation_impedance_rx", None, '"MΩ"', 2, True),
        ("insulation_impedance_ry", None, '"MΩ"', 2, True),
        ("inverter_temperature", "SensorDeviceClass.TEMPERATURE", "UnitOfTemperature.CELSIUS", 0, True),
        ("country_profile_raw", None, None, None, False),
    ]
)
lines = ["ADVANCED_DIAGNOSTIC_SENSORS: tuple[TsunSensorDescription, ...] = ("]
for key, device_class, unit, precision, measurement_state in advanced_specs:
    lines.append("    _advanced_diagnostic(")
    lines.append(f'        "{key}",')
    lines.append(f'        "{key}",')
    if device_class is not None:
        lines.append(f"        device_class={device_class},")
    if unit is not None:
        lines.append(f"        unit={unit},")
    if precision is not None:
        lines.append(f"        precision={precision},")
    if not measurement_state:
        lines.append("        state_class=None,")
    lines.append("    ),")
lines.extend([")", "", ""])
insert_before(psensor, "SENSORS: tuple[TsunSensorDescription, ...] = (\n", "\n".join(lines))
replace_once(
    psensor,
    '    _diagnostic_power("max_designed_power", "max_designed_power"),\n    TsunSensorDescription(\n        key="communication_last_success",',
    '    _diagnostic_power("max_designed_power", "max_designed_power"),\n    *ADVANCED_DIAGNOSTIC_SENSORS,\n    TsunSensorDescription(\n        key="communication_last_success",',
)

# Entity names in all 8 supported languages.
EN = {
    "grid_overvoltage_recovery_voltage": "Grid overvoltage recovery voltage",
    "grid_undervoltage_recovery_voltage": "Grid undervoltage recovery voltage",
    "grid_overfrequency_recovery_frequency": "Grid overfrequency recovery frequency",
    "grid_underfrequency_recovery_frequency": "Grid underfrequency recovery frequency",
    "grid_undervoltage_level_1": "Grid undervoltage level 1",
    "grid_undervoltage_level_2": "Grid undervoltage level 2",
    "grid_undervoltage_level_3": "Grid undervoltage level 3",
    "grid_undervoltage_time_1": "Grid undervoltage time 1",
    "grid_undervoltage_time_2": "Grid undervoltage time 2",
    "grid_undervoltage_time_3": "Grid undervoltage time 3",
    "grid_overvoltage_level_1": "Grid overvoltage level 1",
    "grid_overvoltage_level_2": "Grid overvoltage level 2",
    "grid_overvoltage_time_1": "Grid overvoltage time 1",
    "grid_overvoltage_time_2": "Grid overvoltage time 2",
    "grid_underfrequency_level_1": "Grid underfrequency level 1",
    "grid_underfrequency_level_2": "Grid underfrequency level 2",
    "grid_underfrequency_time_1": "Grid underfrequency time 1",
    "grid_underfrequency_time_2": "Grid underfrequency time 2",
    "grid_overfrequency_level_1": "Grid overfrequency level 1",
    "grid_overfrequency_level_2": "Grid overfrequency level 2",
    "grid_overfrequency_time_1": "Grid overfrequency time 1",
    "grid_overfrequency_time_2": "Grid overfrequency time 2",
    "output_coefficient": "Output coefficient",
    "protocol_version": "Protocol version",
    "inverter_version": "Inverter version",
    "insulation_impedance_rx": "Insulation impedance RX",
    "insulation_impedance_ry": "Insulation impedance RY",
    "inverter_temperature": "Inverter temperature",
    "country_profile_raw": "Country/profile code",
}

TRANSLATIONS = {
    "en": EN,
    "fr": {
        "grid_overvoltage_recovery_voltage": "Tension de rétablissement après surtension réseau",
        "grid_undervoltage_recovery_voltage": "Tension de rétablissement après sous-tension réseau",
        "grid_overfrequency_recovery_frequency": "Fréquence de rétablissement après surfréquence réseau",
        "grid_underfrequency_recovery_frequency": "Fréquence de rétablissement après sous-fréquence réseau",
        "grid_undervoltage_level_1": "Seuil de sous-tension réseau niveau 1",
        "grid_undervoltage_level_2": "Seuil de sous-tension réseau niveau 2",
        "grid_undervoltage_level_3": "Seuil de sous-tension réseau niveau 3",
        "grid_undervoltage_time_1": "Temps de sous-tension réseau niveau 1",
        "grid_undervoltage_time_2": "Temps de sous-tension réseau niveau 2",
        "grid_undervoltage_time_3": "Temps de sous-tension réseau niveau 3",
        "grid_overvoltage_level_1": "Seuil de surtension réseau niveau 1",
        "grid_overvoltage_level_2": "Seuil de surtension réseau niveau 2",
        "grid_overvoltage_time_1": "Temps de surtension réseau niveau 1",
        "grid_overvoltage_time_2": "Temps de surtension réseau niveau 2",
        "grid_underfrequency_level_1": "Seuil de sous-fréquence réseau niveau 1",
        "grid_underfrequency_level_2": "Seuil de sous-fréquence réseau niveau 2",
        "grid_underfrequency_time_1": "Temps de sous-fréquence réseau niveau 1",
        "grid_underfrequency_time_2": "Temps de sous-fréquence réseau niveau 2",
        "grid_overfrequency_level_1": "Seuil de surfréquence réseau niveau 1",
        "grid_overfrequency_level_2": "Seuil de surfréquence réseau niveau 2",
        "grid_overfrequency_time_1": "Temps de surfréquence réseau niveau 1",
        "grid_overfrequency_time_2": "Temps de surfréquence réseau niveau 2",
        "output_coefficient": "Coefficient de sortie",
        "protocol_version": "Version du protocole",
        "inverter_version": "Version de l’onduleur",
        "insulation_impedance_rx": "Impédance d’isolement RX",
        "insulation_impedance_ry": "Impédance d’isolement RY",
        "inverter_temperature": "Température de l’onduleur",
        "country_profile_raw": "Code pays/profil",
    },
    "de": {
        "grid_overvoltage_recovery_voltage": "Netz-Rückkehrspannung nach Überspannung",
        "grid_undervoltage_recovery_voltage": "Netz-Rückkehrspannung nach Unterspannung",
        "grid_overfrequency_recovery_frequency": "Netz-Rückkehrfrequenz nach Überfrequenz",
        "grid_underfrequency_recovery_frequency": "Netz-Rückkehrfrequenz nach Unterfrequenz",
        "grid_undervoltage_level_1": "Netz-Unterspannungsgrenze 1",
        "grid_undervoltage_level_2": "Netz-Unterspannungsgrenze 2",
        "grid_undervoltage_level_3": "Netz-Unterspannungsgrenze 3",
        "grid_undervoltage_time_1": "Netz-Unterspannungszeit 1",
        "grid_undervoltage_time_2": "Netz-Unterspannungszeit 2",
        "grid_undervoltage_time_3": "Netz-Unterspannungszeit 3",
        "grid_overvoltage_level_1": "Netz-Überspannungsgrenze 1",
        "grid_overvoltage_level_2": "Netz-Überspannungsgrenze 2",
        "grid_overvoltage_time_1": "Netz-Überspannungszeit 1",
        "grid_overvoltage_time_2": "Netz-Überspannungszeit 2",
        "grid_underfrequency_level_1": "Netz-Unterfrequenzgrenze 1",
        "grid_underfrequency_level_2": "Netz-Unterfrequenzgrenze 2",
        "grid_underfrequency_time_1": "Netz-Unterfrequenzzeit 1",
        "grid_underfrequency_time_2": "Netz-Unterfrequenzzeit 2",
        "grid_overfrequency_level_1": "Netz-Überfrequenzgrenze 1",
        "grid_overfrequency_level_2": "Netz-Überfrequenzgrenze 2",
        "grid_overfrequency_time_1": "Netz-Überfrequenzzeit 1",
        "grid_overfrequency_time_2": "Netz-Überfrequenzzeit 2",
        "output_coefficient": "Ausgangskoeffizient",
        "protocol_version": "Protokollversion",
        "inverter_version": "Wechselrichterversion",
        "insulation_impedance_rx": "Isolationsimpedanz RX",
        "insulation_impedance_ry": "Isolationsimpedanz RY",
        "inverter_temperature": "Wechselrichtertemperatur",
        "country_profile_raw": "Länder-/Profilcode",
    },
    "nl": {
        "grid_overvoltage_recovery_voltage": "Herstelspanning na netoverspanning",
        "grid_undervoltage_recovery_voltage": "Herstelspanning na netonderspanning",
        "grid_overfrequency_recovery_frequency": "Herstelfrequentie na netoverfrequentie",
        "grid_underfrequency_recovery_frequency": "Herstelfrequentie na netonderfrequentie",
        "grid_undervoltage_level_1": "Netonderspanningsniveau 1",
        "grid_undervoltage_level_2": "Netonderspanningsniveau 2",
        "grid_undervoltage_level_3": "Netonderspanningsniveau 3",
        "grid_undervoltage_time_1": "Netonderspanningstijd 1",
        "grid_undervoltage_time_2": "Netonderspanningstijd 2",
        "grid_undervoltage_time_3": "Netonderspanningstijd 3",
        "grid_overvoltage_level_1": "Netoverspanningsniveau 1",
        "grid_overvoltage_level_2": "Netoverspanningsniveau 2",
        "grid_overvoltage_time_1": "Netoverspanningstijd 1",
        "grid_overvoltage_time_2": "Netoverspanningstijd 2",
        "grid_underfrequency_level_1": "Netonderfrequentieniveau 1",
        "grid_underfrequency_level_2": "Netonderfrequentieniveau 2",
        "grid_underfrequency_time_1": "Netonderfrequentietijd 1",
        "grid_underfrequency_time_2": "Netonderfrequentietijd 2",
        "grid_overfrequency_level_1": "Netoverfrequentieniveau 1",
        "grid_overfrequency_level_2": "Netoverfrequentieniveau 2",
        "grid_overfrequency_time_1": "Netoverfrequentietijd 1",
        "grid_overfrequency_time_2": "Netoverfrequentietijd 2",
        "output_coefficient": "Uitgangscoëfficiënt",
        "protocol_version": "Protocolversie",
        "inverter_version": "Omvormerversie",
        "insulation_impedance_rx": "Isolatie-impedantie RX",
        "insulation_impedance_ry": "Isolatie-impedantie RY",
        "inverter_temperature": "Omvormertemperatuur",
        "country_profile_raw": "Land-/profielcode",
    },
    "it": {
        "grid_overvoltage_recovery_voltage": "Tensione di ripristino dopo sovratensione di rete",
        "grid_undervoltage_recovery_voltage": "Tensione di ripristino dopo sottotensione di rete",
        "grid_overfrequency_recovery_frequency": "Frequenza di ripristino dopo sovrafrequenza di rete",
        "grid_underfrequency_recovery_frequency": "Frequenza di ripristino dopo sottofrequenza di rete",
        "grid_undervoltage_level_1": "Soglia sottotensione rete livello 1",
        "grid_undervoltage_level_2": "Soglia sottotensione rete livello 2",
        "grid_undervoltage_level_3": "Soglia sottotensione rete livello 3",
        "grid_undervoltage_time_1": "Tempo sottotensione rete livello 1",
        "grid_undervoltage_time_2": "Tempo sottotensione rete livello 2",
        "grid_undervoltage_time_3": "Tempo sottotensione rete livello 3",
        "grid_overvoltage_level_1": "Soglia sovratensione rete livello 1",
        "grid_overvoltage_level_2": "Soglia sovratensione rete livello 2",
        "grid_overvoltage_time_1": "Tempo sovratensione rete livello 1",
        "grid_overvoltage_time_2": "Tempo sovratensione rete livello 2",
        "grid_underfrequency_level_1": "Soglia sottofrequenza rete livello 1",
        "grid_underfrequency_level_2": "Soglia sottofrequenza rete livello 2",
        "grid_underfrequency_time_1": "Tempo sottofrequenza rete livello 1",
        "grid_underfrequency_time_2": "Tempo sottofrequenza rete livello 2",
        "grid_overfrequency_level_1": "Soglia sovrafrequenza rete livello 1",
        "grid_overfrequency_level_2": "Soglia sovrafrequenza rete livello 2",
        "grid_overfrequency_time_1": "Tempo sovrafrequenza rete livello 1",
        "grid_overfrequency_time_2": "Tempo sovrafrequenza rete livello 2",
        "output_coefficient": "Coefficiente di uscita",
        "protocol_version": "Versione protocollo",
        "inverter_version": "Versione inverter",
        "insulation_impedance_rx": "Impedenza di isolamento RX",
        "insulation_impedance_ry": "Impedenza di isolamento RY",
        "inverter_temperature": "Temperatura inverter",
        "country_profile_raw": "Codice paese/profilo",
    },
    "es": {
        "grid_overvoltage_recovery_voltage": "Tensión de recuperación tras sobretensión de red",
        "grid_undervoltage_recovery_voltage": "Tensión de recuperación tras subtensión de red",
        "grid_overfrequency_recovery_frequency": "Frecuencia de recuperación tras sobrefrecuencia de red",
        "grid_underfrequency_recovery_frequency": "Frecuencia de recuperación tras subfrecuencia de red",
        "grid_undervoltage_level_1": "Umbral de subtensión de red nivel 1",
        "grid_undervoltage_level_2": "Umbral de subtensión de red nivel 2",
        "grid_undervoltage_level_3": "Umbral de subtensión de red nivel 3",
        "grid_undervoltage_time_1": "Tiempo de subtensión de red nivel 1",
        "grid_undervoltage_time_2": "Tiempo de subtensión de red nivel 2",
        "grid_undervoltage_time_3": "Tiempo de subtensión de red nivel 3",
        "grid_overvoltage_level_1": "Umbral de sobretensión de red nivel 1",
        "grid_overvoltage_level_2": "Umbral de sobretensión de red nivel 2",
        "grid_overvoltage_time_1": "Tiempo de sobretensión de red nivel 1",
        "grid_overvoltage_time_2": "Tiempo de sobretensión de red nivel 2",
        "grid_underfrequency_level_1": "Umbral de subfrecuencia de red nivel 1",
        "grid_underfrequency_level_2": "Umbral de subfrecuencia de red nivel 2",
        "grid_underfrequency_time_1": "Tiempo de subfrecuencia de red nivel 1",
        "grid_underfrequency_time_2": "Tiempo de subfrecuencia de red nivel 2",
        "grid_overfrequency_level_1": "Umbral de sobrefrecuencia de red nivel 1",
        "grid_overfrequency_level_2": "Umbral de sobrefrecuencia de red nivel 2",
        "grid_overfrequency_time_1": "Tiempo de sobrefrecuencia de red nivel 1",
        "grid_overfrequency_time_2": "Tiempo de sobrefrecuencia de red nivel 2",
        "output_coefficient": "Coeficiente de salida",
        "protocol_version": "Versión del protocolo",
        "inverter_version": "Versión del inversor",
        "insulation_impedance_rx": "Impedancia de aislamiento RX",
        "insulation_impedance_ry": "Impedancia de aislamiento RY",
        "inverter_temperature": "Temperatura del inversor",
        "country_profile_raw": "Código de país/perfil",
    },
    "pl": {
        "grid_overvoltage_recovery_voltage": "Napięcie powrotu po przepięciu sieci",
        "grid_undervoltage_recovery_voltage": "Napięcie powrotu po zbyt niskim napięciu sieci",
        "grid_overfrequency_recovery_frequency": "Częstotliwość powrotu po zbyt wysokiej częstotliwości sieci",
        "grid_underfrequency_recovery_frequency": "Częstotliwość powrotu po zbyt niskiej częstotliwości sieci",
        "grid_undervoltage_level_1": "Próg podnapięciowy sieci poziom 1",
        "grid_undervoltage_level_2": "Próg podnapięciowy sieci poziom 2",
        "grid_undervoltage_level_3": "Próg podnapięciowy sieci poziom 3",
        "grid_undervoltage_time_1": "Czas podnapięcia sieci poziom 1",
        "grid_undervoltage_time_2": "Czas podnapięcia sieci poziom 2",
        "grid_undervoltage_time_3": "Czas podnapięcia sieci poziom 3",
        "grid_overvoltage_level_1": "Próg przepięciowy sieci poziom 1",
        "grid_overvoltage_level_2": "Próg przepięciowy sieci poziom 2",
        "grid_overvoltage_time_1": "Czas przepięcia sieci poziom 1",
        "grid_overvoltage_time_2": "Czas przepięcia sieci poziom 2",
        "grid_underfrequency_level_1": "Próg zbyt niskiej częstotliwości poziom 1",
        "grid_underfrequency_level_2": "Próg zbyt niskiej częstotliwości poziom 2",
        "grid_underfrequency_time_1": "Czas zbyt niskiej częstotliwości poziom 1",
        "grid_underfrequency_time_2": "Czas zbyt niskiej częstotliwości poziom 2",
        "grid_overfrequency_level_1": "Próg zbyt wysokiej częstotliwości poziom 1",
        "grid_overfrequency_level_2": "Próg zbyt wysokiej częstotliwości poziom 2",
        "grid_overfrequency_time_1": "Czas zbyt wysokiej częstotliwości poziom 1",
        "grid_overfrequency_time_2": "Czas zbyt wysokiej częstotliwości poziom 2",
        "output_coefficient": "Współczynnik wyjściowy",
        "protocol_version": "Wersja protokołu",
        "inverter_version": "Wersja falownika",
        "insulation_impedance_rx": "Impedancja izolacji RX",
        "insulation_impedance_ry": "Impedancja izolacji RY",
        "inverter_temperature": "Temperatura falownika",
        "country_profile_raw": "Kod kraju/profilu",
    },
    "zh-Hans": {
        "grid_overvoltage_recovery_voltage": "电网过压恢复电压",
        "grid_undervoltage_recovery_voltage": "电网欠压恢复电压",
        "grid_overfrequency_recovery_frequency": "电网过频恢复频率",
        "grid_underfrequency_recovery_frequency": "电网欠频恢复频率",
        "grid_undervoltage_level_1": "电网欠压阈值 1",
        "grid_undervoltage_level_2": "电网欠压阈值 2",
        "grid_undervoltage_level_3": "电网欠压阈值 3",
        "grid_undervoltage_time_1": "电网欠压时间 1",
        "grid_undervoltage_time_2": "电网欠压时间 2",
        "grid_undervoltage_time_3": "电网欠压时间 3",
        "grid_overvoltage_level_1": "电网过压阈值 1",
        "grid_overvoltage_level_2": "电网过压阈值 2",
        "grid_overvoltage_time_1": "电网过压时间 1",
        "grid_overvoltage_time_2": "电网过压时间 2",
        "grid_underfrequency_level_1": "电网欠频阈值 1",
        "grid_underfrequency_level_2": "电网欠频阈值 2",
        "grid_underfrequency_time_1": "电网欠频时间 1",
        "grid_underfrequency_time_2": "电网欠频时间 2",
        "grid_overfrequency_level_1": "电网过频阈值 1",
        "grid_overfrequency_level_2": "电网过频阈值 2",
        "grid_overfrequency_time_1": "电网过频时间 1",
        "grid_overfrequency_time_2": "电网过频时间 2",
        "output_coefficient": "输出系数",
        "protocol_version": "协议版本",
        "inverter_version": "逆变器版本",
        "insulation_impedance_rx": "绝缘阻抗 RX",
        "insulation_impedance_ry": "绝缘阻抗 RY",
        "inverter_temperature": "逆变器温度",
        "country_profile_raw": "国家/配置代码",
    },
}

strings_path = ROOT / "custom_components/tsun_local/strings.json"
strings = json.loads(strings_path.read_text(encoding="utf-8"))
for key, name in EN.items():
    strings["entity"]["sensor"][key] = {"name": name}
strings_path.write_text(json.dumps(strings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

files = {
    "en": "en.json",
    "fr": "fr.json",
    "de": "de.json",
    "nl": "nl.json",
    "it": "it.json",
    "es": "es.json",
    "pl": "pl.json",
    "zh-Hans": "zh-Hans.json",
}
for locale, filename in files.items():
    path = ROOT / "custom_components/tsun_local/translations" / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    for key, name in TRANSLATIONS[locale].items():
        data["entity"]["sensor"][key] = {"name": name}
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Version metadata.
manifest_path = ROOT / "custom_components/tsun_local/manifest.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = VERSION
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Concise README prepared for final 1.4.
README = '''<p align="center">
  <img src="custom_components/tsun_local/brand/icon@2x.png" width="170" alt="TSUN Local">
</p>

<h1 align="center">TSUN Local</h1>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="docs/README_FR.md">Français</a> ·
  <a href="docs/README_DE.md">Deutsch</a> ·
  <a href="docs/README_NL.md">Nederlands</a> ·
  <a href="docs/README_IT.md">Italiano</a> ·
  <a href="docs/README_ES.md">Español</a> ·
  <a href="docs/README_PL.md">Polski</a> ·
  <a href="docs/README_ZH.md">简体中文</a>
</p>

<h3 align="center">Your inverter. Your network. Your data.</h3>
<h2 align="center">Local. Read-only. No cloud. No proxy.</h2>

<p align="center"><strong>Direct local access for compatible TSUN micro-inverters in Home Assistant.</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS Custom" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

<p align="center">Created and maintained by <strong>Jean-Philippe TESTART · <code>jptstar</code></strong><br><em>Built and shared for fun, technical curiosity and the Home Assistant community.</em></p>

> [!IMPORTANT]
> **Unofficial community project.** TSUN Local is independent and is not developed, approved, endorsed or maintained by TSUN.

---

## Your TSUN inverter may already work

TSUN Local communicates directly with compatible TSUN micro-inverters on your LAN and supports several local protocol families.

**Your exact model does not need to be listed to be compatible.**

| Protocol | Known hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Validated |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ Validated |
| **1097** | Compatible GEN3-family devices | 🧪 Experimental |

> **Not listed does not mean unsupported.**

If your inverter uses **1511, 02B0 or 1097**, try it.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Add TSUN Local to HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Install it. Let TSUN Local identify the protocol. See what your inverter exposes.</strong></p>

---

## What you get

### ☀️ PV
Voltage · Current · Power · Daily energy · Total energy

### ⚡ AC
Voltage · Current · Frequency · Power · Daily energy · Total energy

### 🚨 Diagnostics
Alarms · Logger information · Communication state

### 🛡️ Advanced diagnostics
Read-only grid and inverter parameters are exposed where supported. Advanced entities are **disabled by default** and can be enabled individually in Home Assistant.

- **1511:** complete grid-protection diagnostic map.
- **02B0:** complete grid-protection diagnostic map plus output coefficient.
- **1097:** protocol/inverter versions, inverter temperature, insulation impedance RX/RY, country/profile code and designed power where available.

**No inverter configuration writes are implemented.**

---

## Compatibility

**Home Assistant 2026.3.0 or later.**

### ✅ Validated on real hardware

| Model | Protocol | PV inputs |
|---|---|---:|
| **TSOL-MP3000** | 1511 | 6 |
| **TSOL-MX500** | 02B0 | 1 |

### 🔎 Worth trying

**1511 / TITAN**
- TSOL-MP2250
- TSOL-MS3000

**02B0 / GEN3 / GEN3 PLUS**
- MX400 / MX450
- MX800 / MX900 / MX1000
- MX2250
- MS300 / MS350 / MS400
- MS600 / MS700 / MS800
- MS1600 / MS1800 / MS2000
- corresponding `-D` variants where applicable

### 🧪 Experimental

**1097** support is available for testing and needs additional real-hardware validation.

> **Have another TSUN model? Try it. Your feedback can turn it into the next validated device.**

---

## Installation

### HACS
Use the button above, or add `https://github.com/jptstar/tsun-local` as a **Custom repository → Integration** in HACS, download **TSUN Local**, then restart Home Assistant.

### Manual
Copy `custom_components/tsun_local` to `/config/custom_components/`, restart Home Assistant, then add **TSUN Local** from **Settings → Devices & services**.

---

## How it works

- direct local polling;
- no external proxy;
- no TSUN cloud required for telemetry;
- no remote runtime service;
- read-only communication;
- automatic protocol identification where firmware provides a known protocol token;
- forced protocol probing available for compatibility testing.

---

## TSUN Local 1.4

Version 1.4 broadens TSUN Local from individual tested models toward **protocol-family compatibility**.

**1511 · 02B0 · 1097**

It brings automatic protocol identification, progressive PV-input detection, expanded local telemetry, advanced read-only diagnostics, multilingual entity names and easier testing of new TSUN models.

---

## Reverse engineering & validation

The 1511 and 02B0 implementations are developed through **independent local protocol analysis, real-device observation and hardware validation**.

The experimental 1097 mapping was informed by publicly available protocol research from **Stefan Allius / `s-allius/tsun-gen3-proxy`**, then adapted to TSUN Local for direct local use.

---

## License

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distributed under the **GNU General Public License v3.0 or later**. See [LICENSE](LICENSE).
'''
write("README.md", README)

DOCS = {
    "README_FR.md": ("Votre onduleur. Votre réseau. Vos données.", "Local. Lecture seule. Sans cloud. Sans proxy.", "Votre micro-onduleur TSUN fonctionne peut-être déjà", "Un modèle non listé n’est pas forcément incompatible.", "Installez TSUN Local, laissez l’intégration identifier le protocole et voyez les données exposées.", "Diagnostics avancés", "Les paramètres réseau et onduleur en lecture seule sont désactivés par défaut et peuvent être activés individuellement dans Home Assistant.", "Compatibilité", "Validé sur matériel réel", "À tester", "Expérimental", "Vous possédez un autre modèle TSUN ? Essayez-le : il peut devenir le prochain modèle validé.", "Le mapping expérimental 1097 s’appuie sur les recherches publiques de Stefan Allius / s-allius/tsun-gen3-proxy et a été adapté à TSUN Local."),
    "README_DE.md": ("Dein Wechselrichter. Dein Netzwerk. Deine Daten.", "Lokal. Nur lesen. Keine Cloud. Kein Proxy.", "Dein TSUN-Wechselrichter könnte bereits funktionieren", "Nicht aufgeführt bedeutet nicht automatisch nicht unterstützt.", "Installiere TSUN Local, lasse das Protokoll erkennen und prüfe, welche Daten dein Wechselrichter bereitstellt.", "Erweiterte Diagnose", "Schreibgeschützte Netz- und Wechselrichterparameter sind standardmäßig deaktiviert und können in Home Assistant einzeln aktiviert werden.", "Kompatibilität", "Auf echter Hardware validiert", "Ausprobieren", "Experimentell", "Du hast ein anderes TSUN-Modell? Probiere es aus – es könnte das nächste validierte Gerät werden.", "Die experimentelle 1097-Zuordnung basiert auf öffentlich verfügbarer Forschung von Stefan Allius / s-allius/tsun-gen3-proxy und wurde für TSUN Local angepasst."),
    "README_NL.md": ("Jouw omvormer. Jouw netwerk. Jouw data.", "Lokaal. Alleen-lezen. Geen cloud. Geen proxy.", "Jouw TSUN-omvormer werkt mogelijk al", "Niet vermeld betekent niet automatisch niet ondersteund.", "Installeer TSUN Local, laat het protocol herkennen en bekijk welke gegevens je omvormer aanbiedt.", "Geavanceerde diagnostiek", "Alleen-lezen net- en omvormerparameters zijn standaard uitgeschakeld en kunnen afzonderlijk in Home Assistant worden ingeschakeld.", "Compatibiliteit", "Gevalideerd op echte hardware", "Het proberen waard", "Experimenteel", "Heb je een ander TSUN-model? Probeer het: jouw apparaat kan het volgende gevalideerde model worden.", "De experimentele 1097-mapping is gebaseerd op openbaar protocolonderzoek van Stefan Allius / s-allius/tsun-gen3-proxy en aangepast voor TSUN Local."),
    "README_IT.md": ("Il tuo inverter. La tua rete. I tuoi dati.", "Locale. Sola lettura. Nessun cloud. Nessun proxy.", "Il tuo inverter TSUN potrebbe già funzionare", "Non presente nell’elenco non significa non supportato.", "Installa TSUN Local, lascia che identifichi il protocollo e verifica i dati esposti dall’inverter.", "Diagnostica avanzata", "I parametri di rete e inverter in sola lettura sono disattivati per impostazione predefinita e possono essere attivati singolarmente in Home Assistant.", "Compatibilità", "Validato su hardware reale", "Da provare", "Sperimentale", "Hai un altro modello TSUN? Provalo: potrebbe diventare il prossimo dispositivo validato.", "La mappatura sperimentale 1097 si basa sulla ricerca pubblica di Stefan Allius / s-allius/tsun-gen3-proxy ed è stata adattata a TSUN Local."),
    "README_ES.md": ("Tu inversor. Tu red. Tus datos.", "Local. Solo lectura. Sin nube. Sin proxy.", "Tu inversor TSUN puede funcionar ya", "No aparecer en la lista no significa que no sea compatible.", "Instala TSUN Local, deja que identifique el protocolo y comprueba qué datos expone tu inversor.", "Diagnóstico avanzado", "Los parámetros de red e inversor de solo lectura están desactivados por defecto y pueden activarse individualmente en Home Assistant.", "Compatibilidad", "Validado en hardware real", "Vale la pena probar", "Experimental", "¿Tienes otro modelo TSUN? Pruébalo: puede convertirse en el próximo dispositivo validado.", "El mapeo experimental 1097 se basa en la investigación pública de Stefan Allius / s-allius/tsun-gen3-proxy y se ha adaptado a TSUN Local."),
    "README_PL.md": ("Twój falownik. Twoja sieć. Twoje dane.", "Lokalnie. Tylko odczyt. Bez chmury. Bez proxy.", "Twój falownik TSUN może już działać", "Brak modelu na liście nie oznacza braku obsługi.", "Zainstaluj TSUN Local, pozwól wykryć protokół i sprawdź dane udostępniane przez falownik.", "Zaawansowana diagnostyka", "Parametry sieci i falownika tylko do odczytu są domyślnie wyłączone i można je włączać pojedynczo w Home Assistant.", "Kompatybilność", "Zweryfikowano na rzeczywistym sprzęcie", "Warto wypróbować", "Eksperymentalne", "Masz inny model TSUN? Wypróbuj go — może zostać kolejnym zweryfikowanym urządzeniem.", "Eksperymentalna mapa 1097 korzysta z publicznych badań Stefana Alliusa / s-allius/tsun-gen3-proxy i została dostosowana do TSUN Local."),
    "README_ZH.md": ("你的逆变器。你的网络。你的数据。", "本地。只读。无需云端。无需代理。", "你的 TSUN 逆变器可能已经可以使用", "未列出的型号并不代表不受支持。", "安装 TSUN Local，让它识别协议，然后查看逆变器可提供的数据。", "高级诊断", "只读的电网和逆变器参数默认关闭，可在 Home Assistant 中逐项启用。", "兼容性", "已在真实硬件上验证", "值得尝试", "实验性", "有其他 TSUN 型号？试试看——它可能成为下一个已验证设备。", "实验性 1097 映射参考了 Stefan Allius / s-allius/tsun-gen3-proxy 的公开协议研究，并针对 TSUN Local 进行了适配。"),
}
LANG_LINKS = "[English](../README.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [Nederlands](README_NL.md) · [Italiano](README_IT.md) · [Español](README_ES.md) · [Polski](README_PL.md) · [简体中文](README_ZH.md)"
for filename, values in DOCS.items():
    s1, s2, may, notlisted, install, advanced, advtext, compat, validated, trying, experimental, other, credit = values
    page = f'''# TSUN Local

<p align="center">{LANG_LINKS}</p>

### {s1}
## {s2}

> **{may}**  
> {notlisted}

| Protocol | Hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ {validated} |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ {validated} |
| **1097** | GEN3 family | 🧪 {experimental} |

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

**{install}**

## {advanced}

{advtext}

- **1511:** grid protection diagnostics
- **02B0:** grid protection diagnostics + output coefficient
- **1097:** protocol/inverter versions, temperature, insulation impedance RX/RY, country/profile code and designed power

## {compat}

### ✅ {validated}
- **TSOL-MP3000** — 1511 — 6 PV inputs
- **TSOL-MX500** — 02B0 — 1 PV input

### 🔎 {trying}
MP2250 · MS3000 · MX400 · MX450 · MX800 · MX900 · MX1000 · MX2250 · MS300 · MS350 · MS400 · MS600 · MS700 · MS800 · MS1600 · MS1800 · MS2000 and corresponding `-D` variants where applicable.

### 🧪 1097 — {experimental}

{other}

---

**Jean-Philippe TESTART (`jptstar`)** · Unofficial independent community project · GPL-3.0-or-later

{credit}
'''
    write(f"docs/{filename}", page)

# Changelog.
changelog = read("CHANGELOG.md")
section = '''## [1.4.0-beta.8] - 2026-08-17

### Added

- complete read-only advanced grid-protection diagnostics for the 1511 and 02B0 protocol families;
- read-only 02B0 output coefficient diagnostic;
- experimental 1097 diagnostics for protocol/inverter versions, inverter temperature, insulation impedance RX/RY and raw country/profile code;
- advanced diagnostic entity names in English, French, German, Dutch, Italian, Spanish, Polish and Simplified Chinese;
- a concise 1.4-ready README focused on local access and protocol-family compatibility.

### Fixed

- correct 1511 per-PV daily-energy register offsets from `base + 4` to `base + 5` for PV1 through PV6;
- use the corrected daily-energy positions when detecting populated 1511 PV inputs.

### Changed

- advanced diagnostics are categorized as diagnostic entities and disabled by default so normal installations stay uncluttered;
- the experimental 1097 diagnostics continue to credit the public `s-allius/tsun-gen3-proxy` protocol research by Stefan Allius.

### Safety

- all newly added diagnostics are read-only;
- the 02B0 output coefficient is read but never written;
- no inverter configuration or control write has been added.

'''
marker = "## [1.4.0-beta.7]"
if marker not in changelog:
    raise RuntimeError("beta.7 changelog marker not found")
write("CHANGELOG.md", changelog.replace(marker, section + marker, 1))

# Focused regression tests.
TEST = '''# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

PROTOCOLS_PATH = Path(__file__).parents[1] / "custom_components" / "tsun_local" / "protocols"
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_beta8_protocol_tests",
    PROTOCOLS_PATH / "__init__.py",
    submodule_search_locations=[str(PROTOCOLS_PATH)],
)
assert SPEC is not None and SPEC.loader is not None
PKG = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PKG
SPEC.loader.exec_module(PKG)

from tsun_local_beta8_protocol_tests.protocol_1511 import decode_advanced_diagnostics as decode_1511_advanced, decode_measurements as decode_1511, detect_pv_count as detect_1511_pv_count  # noqa: E402,E501
from tsun_local_beta8_protocol_tests.protocol_02b0 import DIAGNOSTIC_BLOCKS as BLOCKS_02B0_DIAGNOSTIC, decode_advanced_diagnostics as decode_02b0_advanced  # noqa: E402,E501
from tsun_local_beta8_protocol_tests.protocol_1097 import DIAGNOSTIC_BLOCKS as BLOCKS_1097_DIAGNOSTIC, decode_advanced_diagnostics as decode_1097_advanced  # noqa: E402,E501


class Beta8AdvancedDiagnosticsTests(unittest.TestCase):
    def test_1511_daily_energy_uses_base_plus_five(self) -> None:
        registers = {
            0x0BB8: 1, 0x0BC4: 2300, 0x0BC5: 100, 0x0BC7: 5000,
            0x0BC9: 0, 0x0BCC: 3000, 0x0BCD: 1000, 0x0BCE: 100,
            0x0BCF: 0, 0x0BD0: 100, 0x0E10: 350, 0x0E11: 300,
            0x0E12: 1000, 0x0E15: 130, 0x0E28: 0, 0x0E29: 100,
        }
        self.assertEqual(decode_1511(registers, 1)["pv1_energy_today"], 1.3)
        self.assertEqual(detect_1511_pv_count({0x0EEB: 1}), 6)

    def test_1511_grid_diagnostics(self) -> None:
        data = decode_1511_advanced({0x07D4: 2510, 0x07DB: 62, 0x07EA: 340})
        self.assertEqual(data["grid_overvoltage_recovery_voltage"], 251.0)
        self.assertEqual(data["grid_undervoltage_time_1"], 1.24)
        self.assertEqual(data["grid_undervoltage_level_3"], 34.0)

    def test_02b0_grid_diagnostics_and_output_coefficient(self) -> None:
        self.assertIn((0x03, 0x2014, 0x202C), BLOCKS_02B0_DIAGNOSTIC)
        data = decode_02b0_advanced({0x2014: 2510, 0x2028: 16, 0x202C: 80})
        self.assertEqual(data["grid_overvoltage_recovery_voltage"], 251.0)
        self.assertEqual(data["grid_overfrequency_time_1"], 0.32)
        self.assertEqual(data["output_coefficient"], 80.0)

    def test_1097_advanced_diagnostics(self) -> None:
        self.assertIn((0x03, 0x1400, 0x1400), BLOCKS_1097_DIAGNOSTIC)
        data = decode_1097_advanced({0x100A: 0x1234, 0x100C: 0x210A, 0x1216: 1234, 0x1217: 567, 0x1218: 65, 0x1400: 8})
        self.assertEqual(data["protocol_version"], "V1.2.34")
        self.assertEqual(data["inverter_version"], "V2.1.0A")
        self.assertEqual(data["insulation_impedance_rx"], 12.34)
        self.assertEqual(data["insulation_impedance_ry"], 5.67)
        self.assertEqual(data["inverter_temperature"], 25)
        self.assertEqual(data["country_profile_raw"], 8)


if __name__ == "__main__":
    unittest.main()
'''
write("tests/test_beta8_advanced_diagnostics.py", TEST)

# Public-source hygiene check. Construct the private term so it is never stored literally here.
forbidden = "A" + "PK"
for path in ROOT.rglob("*"):
    if not path.is_file() or ".git" in path.parts or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".ico"}:
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    if forbidden.lower() in text.lower():
        raise RuntimeError(f"Private provenance term found in {path}")

print("beta.8 preparation complete")
