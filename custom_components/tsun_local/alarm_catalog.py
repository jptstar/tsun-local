# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Protocol-aware TSUN Local alarm catalogues and localized decoder."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AlarmSource:
    """Describe one locally read 16-bit alarm word."""

    key: str
    category: str
    pv_input: int | None = None


@dataclass(frozen=True, slots=True)
class AlarmDefinition:
    """Describe one stable position in one protocol alarm catalogue."""

    protocol: str
    identifier: str
    source_key: str
    bit: int
    category: str
    pv_input: int | None
    semantic_key: str | None

    @property
    def identified(self) -> bool:
        """Return whether this position has a functional meaning."""
        return self.semantic_key is not None


@dataclass(frozen=True, slots=True)
class ActiveAlarm:
    """One currently active, locally decoded alarm."""

    identifier: str
    name: str
    identified: bool


_PROTOCOL_LABELS = {
    "1511": "1511",
    "02b0": "02B0",
    "1097": "1097",
}

ALARM_SOURCES_BY_PROTOCOL: dict[str, tuple[AlarmSource, ...]] = {
    "1511": (
        *(AlarmSource(f"alarm_global_{index}_raw", "inverter") for index in range(4)),
        *(
            AlarmSource(f"alarm_secondary_{index}_raw", "controller")
            for index in range(4)
        ),
        *(AlarmSource(f"pv{number}_alarm_raw", "pv", number) for number in range(1, 7)),
    ),
    "02b0": tuple(
        AlarmSource(f"alarm_code_{index}_raw", "inverter")
        for index in range(1, 5)
    ),
    "1097": tuple(
        AlarmSource(f"alarm_code_{index}_raw", "inverter")
        for index in range(1, 5)
    ),
}

# 1511 meanings are limited to direct hardware observations.
_IDENTIFIED_1511: dict[tuple[str, int], str] = {
    **{
        (f"pv{number}_alarm_raw", 8): "pv_input_undervoltage"
        for number in range(1, 7)
    },
    **{
        (f"pv{number}_alarm_raw", 10): "pv_dsp_fault"
        for number in range(1, 7)
    },
}

# 02B0 and 1097 expose the same four event words through their respective
# Modbus maps. Unknown/reserved positions intentionally remain unnamed.
_IDENTIFIED_GEN3: dict[tuple[str, int], str] = {
    ("alarm_code_1_raw", 0): "h_bridge_fault",
    ("alarm_code_1_raw", 1): "drive_voltage_fault",
    ("alarm_code_1_raw", 2): "gfdi_fault",
    ("alarm_code_1_raw", 3): "overtemperature",
    ("alarm_code_1_raw", 4): "communication_lost",
    ("alarm_code_1_raw", 7): "eeprom_fault",
    ("alarm_code_1_raw", 8): "no_utility",
    ("alarm_code_1_raw", 9): "grid_voltage_offset",
    ("alarm_code_1_raw", 10): "relay_open",
    ("alarm_code_1_raw", 11): "relay_short",
    ("alarm_code_1_raw", 12): "grid_overvoltage",
    ("alarm_code_1_raw", 13): "grid_undervoltage",
    ("alarm_code_1_raw", 14): "grid_overfrequency",
    ("alarm_code_1_raw", 15): "grid_underfrequency",
    ("alarm_code_2_raw", 0): "pv_overvoltage",
    ("alarm_code_2_raw", 1): "pv_undervoltage",
    ("alarm_code_2_raw", 2): "pv_overcurrent",
    ("alarm_code_2_raw", 3): "pv_ofv_fault",
    ("alarm_code_2_raw", 4): "dc_short_circuit",
}

_IDENTIFIED_POSITIONS_BY_PROTOCOL = {
    "1511": _IDENTIFIED_1511,
    "02b0": _IDENTIFIED_GEN3,
    "1097": _IDENTIFIED_GEN3,
}


def _build_catalogue(protocol: str) -> tuple[AlarmDefinition, ...]:
    """Build one complete protocol catalogue with stable public identifiers."""
    definitions: list[AlarmDefinition] = []
    position = 1
    label = _PROTOCOL_LABELS[protocol]
    identified = _IDENTIFIED_POSITIONS_BY_PROTOCOL[protocol]
    for source in ALARM_SOURCES_BY_PROTOCOL[protocol]:
        for bit in range(16):
            source_position = (source.key, bit)
            definitions.append(
                AlarmDefinition(
                    protocol=protocol,
                    identifier=f"{label}-A{position:03d}",
                    source_key=source.key,
                    bit=bit,
                    category=source.category,
                    pv_input=source.pv_input,
                    semantic_key=identified.get(source_position),
                )
            )
            position += 1
    return tuple(definitions)


ALARM_CATALOGUES = {
    protocol: _build_catalogue(protocol)
    for protocol in ALARM_SOURCES_BY_PROTOCOL
}
ALARM_BY_PROTOCOL_POSITION = {
    protocol: {
        (definition.source_key, definition.bit): definition
        for definition in definitions
    }
    for protocol, definitions in ALARM_CATALOGUES.items()
}

# Backwards-compatible aliases for the original 1511 catalogue API.
ALARM_SOURCES = ALARM_SOURCES_BY_PROTOCOL["1511"]
ALARM_CATALOGUE = ALARM_CATALOGUES["1511"]
ALARM_BY_POSITION = ALARM_BY_PROTOCOL_POSITION["1511"]

_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "pv_input_undervoltage": "PV{pv} input voltage too low",
        "pv_dsp_fault": "PV{pv} DSP fault",
        "h_bridge_fault": "H-bridge fault",
        "drive_voltage_fault": "Drive voltage fault",
        "gfdi_fault": "GFDI fault",
        "overtemperature": "Overtemperature",
        "communication_lost": "Communication lost",
        "eeprom_fault": "EEPROM fault",
        "no_utility": "Grid unavailable",
        "grid_voltage_offset": "Grid voltage offset",
        "relay_open": "Relay open fault",
        "relay_short": "Relay short-circuit fault",
        "grid_overvoltage": "Grid overvoltage",
        "grid_undervoltage": "Grid undervoltage",
        "grid_overfrequency": "Grid overfrequency",
        "grid_underfrequency": "Grid underfrequency",
        "pv_overvoltage": "PV overvoltage",
        "pv_undervoltage": "PV undervoltage",
        "pv_overcurrent": "PV overcurrent",
        "pv_ofv_fault": "PV OFV fault",
        "dc_short_circuit": "DC short circuit",
        "no_active_alarm": "No active alarm",
        "unknown_inverter": "Unidentified inverter alarm",
        "unknown_controller": "Unidentified controller alarm",
        "unknown_pv": "Unidentified PV{pv} alarm",
    },
    "fr": {
        "pv_input_undervoltage": "Tension d’entrée PV{pv} trop faible",
        "pv_dsp_fault": "Défaut du DSP PV{pv}",
        "h_bridge_fault": "Défaut du pont en H",
        "drive_voltage_fault": "Défaut de tension de commande",
        "gfdi_fault": "Défaut GFDI",
        "overtemperature": "Surchauffe",
        "communication_lost": "Communication perdue",
        "eeprom_fault": "Défaut EEPROM",
        "no_utility": "Réseau absent",
        "grid_voltage_offset": "Décalage de tension réseau",
        "relay_open": "Défaut relais ouvert",
        "relay_short": "Défaut relais en court-circuit",
        "grid_overvoltage": "Surtension réseau",
        "grid_undervoltage": "Sous-tension réseau",
        "grid_overfrequency": "Surfréquence réseau",
        "grid_underfrequency": "Sous-fréquence réseau",
        "pv_overvoltage": "Surtension PV",
        "pv_undervoltage": "Sous-tension PV",
        "pv_overcurrent": "Surintensité PV",
        "pv_ofv_fault": "Défaut PV OFV",
        "dc_short_circuit": "Court-circuit DC",
        "no_active_alarm": "Aucune alarme active",
        "unknown_inverter": "Alarme onduleur non identifiée",
        "unknown_controller": "Alarme contrôleur non identifiée",
        "unknown_pv": "Alarme PV{pv} non identifiée",
    },
    "de": {
        "pv_input_undervoltage": "PV{pv}-Eingangsspannung zu niedrig",
        "pv_dsp_fault": "PV{pv}-DSP-Fehler",
        "h_bridge_fault": "H-Brücken-Fehler",
        "drive_voltage_fault": "Treiber-Spannungsfehler",
        "gfdi_fault": "GFDI-Fehler",
        "overtemperature": "Übertemperatur",
        "communication_lost": "Kommunikation verloren",
        "eeprom_fault": "EEPROM-Fehler",
        "no_utility": "Netz nicht verfügbar",
        "grid_voltage_offset": "Netzspannungs-Offset",
        "relay_open": "Relais-Offen-Fehler",
        "relay_short": "Relais-Kurzschlussfehler",
        "grid_overvoltage": "Netzüberspannung",
        "grid_undervoltage": "Netzunterspannung",
        "grid_overfrequency": "Netzüberfrequenz",
        "grid_underfrequency": "Netzunterfrequenz",
        "pv_overvoltage": "PV-Überspannung",
        "pv_undervoltage": "PV-Unterspannung",
        "pv_overcurrent": "PV-Überstrom",
        "pv_ofv_fault": "PV-OFV-Fehler",
        "dc_short_circuit": "DC-Kurzschluss",
        "no_active_alarm": "Kein aktiver Alarm",
        "unknown_inverter": "Nicht identifizierter Wechselrichteralarm",
        "unknown_controller": "Nicht identifizierter Steuerungsalarm",
        "unknown_pv": "Nicht identifizierter PV{pv}-Alarm",
    },
    "es": {
        "pv_input_undervoltage": "Tensión de entrada PV{pv} demasiado baja",
        "pv_dsp_fault": "Fallo del DSP de PV{pv}",
        "h_bridge_fault": "Fallo del puente H",
        "drive_voltage_fault": "Fallo de tensión de control",
        "gfdi_fault": "Fallo GFDI",
        "overtemperature": "Sobretemperatura",
        "communication_lost": "Comunicación perdida",
        "eeprom_fault": "Fallo de EEPROM",
        "no_utility": "Red no disponible",
        "grid_voltage_offset": "Desviación de tensión de red",
        "relay_open": "Fallo de relé abierto",
        "relay_short": "Cortocircuito de relé",
        "grid_overvoltage": "Sobretensión de red",
        "grid_undervoltage": "Subtensión de red",
        "grid_overfrequency": "Sobrefrecuencia de red",
        "grid_underfrequency": "Subfrecuencia de red",
        "pv_overvoltage": "Sobretensión PV",
        "pv_undervoltage": "Subtensión PV",
        "pv_overcurrent": "Sobrecorriente PV",
        "pv_ofv_fault": "Fallo PV OFV",
        "dc_short_circuit": "Cortocircuito DC",
        "no_active_alarm": "Ninguna alarma activa",
        "unknown_inverter": "Alarma del inversor sin identificar",
        "unknown_controller": "Alarma del controlador sin identificar",
        "unknown_pv": "Alarma de PV{pv} sin identificar",
    },
    "it": {
        "pv_input_undervoltage": "Tensione di ingresso PV{pv} troppo bassa",
        "pv_dsp_fault": "Guasto DSP PV{pv}",
        "h_bridge_fault": "Guasto ponte H",
        "drive_voltage_fault": "Guasto tensione di pilotaggio",
        "gfdi_fault": "Guasto GFDI",
        "overtemperature": "Sovratemperatura",
        "communication_lost": "Comunicazione persa",
        "eeprom_fault": "Guasto EEPROM",
        "no_utility": "Rete non disponibile",
        "grid_voltage_offset": "Offset tensione di rete",
        "relay_open": "Guasto relè aperto",
        "relay_short": "Cortocircuito relè",
        "grid_overvoltage": "Sovratensione di rete",
        "grid_undervoltage": "Sottotensione di rete",
        "grid_overfrequency": "Sovrafrequenza di rete",
        "grid_underfrequency": "Sottofrequenza di rete",
        "pv_overvoltage": "Sovratensione PV",
        "pv_undervoltage": "Sottotensione PV",
        "pv_overcurrent": "Sovracorrente PV",
        "pv_ofv_fault": "Guasto PV OFV",
        "dc_short_circuit": "Cortocircuito DC",
        "no_active_alarm": "Nessun allarme attivo",
        "unknown_inverter": "Allarme inverter non identificato",
        "unknown_controller": "Allarme controller non identificato",
        "unknown_pv": "Allarme PV{pv} non identificato",
    },
    "nl": {
        "pv_input_undervoltage": "PV{pv}-ingangsspanning te laag",
        "pv_dsp_fault": "PV{pv}-DSP-storing",
        "h_bridge_fault": "H-brugstoring",
        "drive_voltage_fault": "Aanstuurspanningsfout",
        "gfdi_fault": "GFDI-storing",
        "overtemperature": "Overtemperatuur",
        "communication_lost": "Communicatie verloren",
        "eeprom_fault": "EEPROM-storing",
        "no_utility": "Net niet beschikbaar",
        "grid_voltage_offset": "Netspanningsafwijking",
        "relay_open": "Relais-open-storing",
        "relay_short": "Relais-kortsluiting",
        "grid_overvoltage": "Netoverspanning",
        "grid_undervoltage": "Netonderspanning",
        "grid_overfrequency": "Netoverfrequentie",
        "grid_underfrequency": "Netonderfrequentie",
        "pv_overvoltage": "PV-overspanning",
        "pv_undervoltage": "PV-onderspanning",
        "pv_overcurrent": "PV-overstroom",
        "pv_ofv_fault": "PV-OFV-storing",
        "dc_short_circuit": "DC-kortsluiting",
        "no_active_alarm": "Geen actief alarm",
        "unknown_inverter": "Niet-geïdentificeerd omvormeralarm",
        "unknown_controller": "Niet-geïdentificeerd besturingsalarm",
        "unknown_pv": "Niet-geïdentificeerd PV{pv}-alarm",
    },
    "pl": {
        "pv_input_undervoltage": "Zbyt niskie napięcie wejściowe PV{pv}",
        "pv_dsp_fault": "Usterka DSP PV{pv}",
        "h_bridge_fault": "Usterka mostka H",
        "drive_voltage_fault": "Usterka napięcia sterowania",
        "gfdi_fault": "Usterka GFDI",
        "overtemperature": "Przegrzanie",
        "communication_lost": "Utrata komunikacji",
        "eeprom_fault": "Usterka EEPROM",
        "no_utility": "Brak sieci",
        "grid_voltage_offset": "Przesunięcie napięcia sieci",
        "relay_open": "Usterka otwartego przekaźnika",
        "relay_short": "Zwarcie przekaźnika",
        "grid_overvoltage": "Przepięcie sieci",
        "grid_undervoltage": "Zbyt niskie napięcie sieci",
        "grid_overfrequency": "Zbyt wysoka częstotliwość sieci",
        "grid_underfrequency": "Zbyt niska częstotliwość sieci",
        "pv_overvoltage": "Przepięcie PV",
        "pv_undervoltage": "Zbyt niskie napięcie PV",
        "pv_overcurrent": "Przeciążenie prądowe PV",
        "pv_ofv_fault": "Usterka PV OFV",
        "dc_short_circuit": "Zwarcie DC",
        "no_active_alarm": "Brak aktywnych alarmów",
        "unknown_inverter": "Nierozpoznany alarm falownika",
        "unknown_controller": "Nierozpoznany alarm sterownika",
        "unknown_pv": "Nierozpoznany alarm PV{pv}",
    },
    "zh-hans": {
        "pv_input_undervoltage": "PV{pv} 输入电压过低",
        "pv_dsp_fault": "PV{pv} DSP 故障",
        "h_bridge_fault": "H 桥故障",
        "drive_voltage_fault": "驱动电压故障",
        "gfdi_fault": "GFDI 故障",
        "overtemperature": "温度过高",
        "communication_lost": "通信丢失",
        "eeprom_fault": "EEPROM 故障",
        "no_utility": "电网不可用",
        "grid_voltage_offset": "电网电压偏移",
        "relay_open": "继电器开路故障",
        "relay_short": "继电器短路故障",
        "grid_overvoltage": "电网过压",
        "grid_undervoltage": "电网欠压",
        "grid_overfrequency": "电网频率过高",
        "grid_underfrequency": "电网频率过低",
        "pv_overvoltage": "PV 过压",
        "pv_undervoltage": "PV 欠压",
        "pv_overcurrent": "PV 过流",
        "pv_ofv_fault": "PV OFV 故障",
        "dc_short_circuit": "直流短路",
        "no_active_alarm": "无活动报警",
        "unknown_inverter": "未识别的逆变器报警",
        "unknown_controller": "未识别的控制器报警",
        "unknown_pv": "未识别的 PV{pv} 报警",
    },
}


def _normalize_protocol(protocol: str | None) -> str:
    """Return a supported lower-case protocol identifier."""
    normalized = (protocol or "1511").lower()
    return normalized if normalized in ALARM_CATALOGUES else "1511"


def _protocol_from_measurements(measurements: dict[str, Any]) -> str:
    """Resolve the active protocol from coordinator metadata or source keys."""
    protocol = measurements.get("_alarm_protocol")
    if isinstance(protocol, str) and protocol.lower() in ALARM_CATALOGUES:
        return protocol.lower()
    if any(source.key in measurements for source in ALARM_SOURCES_BY_PROTOCOL["1511"]):
        return "1511"
    return "02b0"


def _language_texts(language: str) -> dict[str, str]:
    """Return the closest supported language, with English as fallback."""
    normalized = language.replace("_", "-").lower()
    return (
        _TEXTS.get(normalized)
        or _TEXTS.get(normalized.split("-", 1)[0])
        or _TEXTS["en"]
    )


def _alarm_name(definition: AlarmDefinition, language: str) -> str:
    """Return localized wording followed by the stable protocol position."""
    texts = _language_texts(language)
    if definition.semantic_key is not None:
        template = texts[definition.semantic_key]
    else:
        template = texts[f"unknown_{definition.category}"]
    description = template.format(
        pv=definition.pv_input if definition.pv_input is not None else "",
    )
    return f"{description} ({definition.identifier})"


def decode_active_alarms(
    measurements: dict[str, Any],
    language: str,
    protocol: str | None = None,
) -> tuple[ActiveAlarm, ...]:
    """Decode every active bit in the selected protocol catalogue."""
    selected = _normalize_protocol(
        protocol if protocol is not None else _protocol_from_measurements(measurements)
    )
    active: list[ActiveAlarm] = []
    for source in ALARM_SOURCES_BY_PROTOCOL[selected]:
        value = measurements.get(source.key)
        if not isinstance(value, int):
            continue
        for bit in range(16):
            if not value & (1 << bit):
                continue
            definition = ALARM_BY_PROTOCOL_POSITION[selected][(source.key, bit)]
            active.append(
                ActiveAlarm(
                    identifier=definition.identifier,
                    name=_alarm_name(definition, language),
                    identified=definition.identified,
                )
            )
    return tuple(active)


def active_alarm_state(
    measurements: dict[str, Any],
    language: str,
    protocol: str | None = None,
) -> str:
    """Return a localized, bounded state string for active alarm names."""
    active = decode_active_alarms(measurements, language, protocol)
    if not active:
        return _language_texts(language)["no_active_alarm"]

    names = [alarm.name for alarm in active]
    state = names[0]
    for index, name in enumerate(names[1:], start=1):
        candidate = f"{state} · {name}"
        if len(candidate) <= 255:
            state = candidate
            continue
        remaining = len(names) - index
        suffix = f" · +{remaining}"
        room = max(0, 255 - len(suffix))
        return f"{state[:room].rstrip()}{suffix}"[:255]
    return state[:255]


def alarm_state_attributes(
    measurements: dict[str, Any],
    language: str,
    protocol: str | None = None,
) -> dict[str, Any]:
    """Return compact Home Assistant attributes for active alarms."""
    active = decode_active_alarms(measurements, language, protocol)
    return {
        "active_alarm_names": [alarm.name for alarm in active],
        "active_alarm_codes": [alarm.identifier for alarm in active],
    }
