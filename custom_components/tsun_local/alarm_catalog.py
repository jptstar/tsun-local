# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Independent MP3000 alarm catalogue and local decoder.

All fourteen 16-bit words have a stable local position. Functional wording is
shown whenever a MP3000/TITAN mapping is available. Hardware-validation status
is kept separately so Home Assistant can show useful names without presenting
candidate mappings as physically confirmed.
"""

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
    """Describe one stable position in the independent alarm catalogue."""

    identifier: str
    source_key: str
    bit: int
    category: str
    pv_input: int | None
    semantic_key: str | None
    validated: bool

    @property
    def identified(self) -> bool:
        """Return whether this position has been physically validated."""
        return self.validated


@dataclass(frozen=True, slots=True)
class ActiveAlarm:
    """One currently active, locally decoded alarm."""

    identifier: str
    name: str
    identified: bool


ALARM_SOURCES: tuple[AlarmSource, ...] = (
    *(AlarmSource(f"alarm_global_{index}_raw", "inverter") for index in range(4)),
    *(
        AlarmSource(f"alarm_secondary_{index}_raw", "controller")
        for index in range(4)
    ),
    *(AlarmSource(f"pv{number}_alarm_raw", "pv", number) for number in range(1, 7)),
)

# MP3000/TITAN functional names recovered from the user's Talent alarm CSV.
#
# The PV rule sequence is consistent across PV1..PV6. Positions not yet observed
# directly on hardware are intentionally named here but tracked separately as
# unvalidated. Validation status belongs in documentation, not in the HA label.
_NAMED_POSITIONS: dict[tuple[str, int], str] = {
    ("alarm_global_0_raw", 0): "grid_undervoltage",
    ("alarm_secondary_0_raw", 0): "dsp_initialization_incomplete",
    ("alarm_secondary_0_raw", 4): "cpu2_communication_lost",
    ("alarm_secondary_0_raw", 6): "dsp_communication_lost",
    **{
        (f"pv{number}_alarm_raw", bit): semantic_key
        for number in range(1, 7)
        for bit, semantic_key in (
            (1, "pv_output_overvoltage"),
            (2, "pv_output_overcurrent"),
            (3, "pv_input_overvoltage"),
            (5, "pv_self_test_fault"),
            (6, "pv_watchdog_reset"),
            (7, "pv_bus_overvoltage"),
            (8, "pv_input_undervoltage"),
            (10, "pv_dsp_fault"),
        )
    },
}

# These twelve positions are supported by direct physical observations.
_VALIDATED_POSITIONS = frozenset(
    (f"pv{number}_alarm_raw", bit)
    for number in range(1, 7)
    for bit in (8, 10)
)


def _build_catalogue() -> tuple[AlarmDefinition, ...]:
    """Build the complete 14 x 16 catalogue with stable identifiers."""
    definitions: list[AlarmDefinition] = []
    position = 1
    for source in ALARM_SOURCES:
        for bit in range(16):
            source_position = (source.key, bit)
            definitions.append(
                AlarmDefinition(
                    identifier=f"A{position:03d}",
                    source_key=source.key,
                    bit=bit,
                    category=source.category,
                    pv_input=source.pv_input,
                    semantic_key=_NAMED_POSITIONS.get(source_position),
                    validated=source_position in _VALIDATED_POSITIONS,
                )
            )
            position += 1
    return tuple(definitions)


ALARM_CATALOGUE = _build_catalogue()
ALARM_BY_POSITION = {
    (definition.source_key, definition.bit): definition
    for definition in ALARM_CATALOGUE
}

_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        "grid_undervoltage": "Grid voltage too low",
        "dsp_initialization_incomplete": "DSP initialization incomplete",
        "cpu2_communication_lost": "CPU2 communication lost",
        "dsp_communication_lost": "DSP communication lost",
        "pv_output_overvoltage": "PV{pv} output overvoltage",
        "pv_output_overcurrent": "PV{pv} output overcurrent",
        "pv_input_overvoltage": "PV{pv} input overvoltage",
        "pv_self_test_fault": "PV{pv} self-test fault",
        "pv_watchdog_reset": "PV{pv} watchdog reset",
        "pv_bus_overvoltage": "PV{pv} bus overvoltage",
        "pv_input_undervoltage": "PV{pv} input voltage too low",
        "pv_dsp_fault": "PV{pv} DSP fault",
        "unknown_inverter": "Unidentified inverter alarm ({code})",
        "unknown_controller": "Unidentified controller alarm ({code})",
        "unknown_pv": "Unidentified PV{pv} alarm ({code})",
    },
    "fr": {
        "grid_undervoltage": "Sous-tension du réseau électrique",
        "dsp_initialization_incomplete": "Initialisation du DSP incomplète",
        "cpu2_communication_lost": "Communication CPU2 perdue",
        "dsp_communication_lost": "Communication DSP perdue",
        "pv_output_overvoltage": "Surtension de sortie PV{pv}",
        "pv_output_overcurrent": "Surintensité de sortie PV{pv}",
        "pv_input_overvoltage": "Surtension d’entrée PV{pv}",
        "pv_self_test_fault": "Défaut d’auto-test PV{pv}",
        "pv_watchdog_reset": "Réinitialisation du chien de garde PV{pv}",
        "pv_bus_overvoltage": "Surtension du bus PV{pv}",
        "pv_input_undervoltage": "Tension d’entrée PV{pv} trop faible",
        "pv_dsp_fault": "Défaut du DSP PV{pv}",
        "unknown_inverter": "Alarme onduleur non identifiée ({code})",
        "unknown_controller": "Alarme contrôleur non identifiée ({code})",
        "unknown_pv": "Alarme PV{pv} non identifiée ({code})",
    },
    "de": {
        "grid_undervoltage": "Unterspannung im Stromnetz",
        "dsp_initialization_incomplete": "DSP-Initialisierung unvollständig",
        "cpu2_communication_lost": "CPU2-Kommunikation verloren",
        "dsp_communication_lost": "DSP-Kommunikation verloren",
        "pv_output_overvoltage": "PV{pv}-Ausgangsüberspannung",
        "pv_output_overcurrent": "PV{pv}-Ausgangsüberstrom",
        "pv_input_overvoltage": "PV{pv}-Eingangsüberspannung",
        "pv_self_test_fault": "PV{pv}-Selbsttestfehler",
        "pv_watchdog_reset": "PV{pv}-Watchdog zurückgesetzt",
        "pv_bus_overvoltage": "PV{pv}-Busüberspannung",
        "pv_input_undervoltage": "PV{pv}-Eingangsspannung zu niedrig",
        "pv_dsp_fault": "PV{pv}-DSP-Fehler",
        "unknown_inverter": "Nicht identifizierter Wechselrichteralarm ({code})",
        "unknown_controller": "Nicht identifizierter Steuerungsalarm ({code})",
        "unknown_pv": "Nicht identifizierter PV{pv}-Alarm ({code})",
    },
    "es": {
        "grid_undervoltage": "Tensión de red demasiado baja",
        "dsp_initialization_incomplete": "Inicialización del DSP incompleta",
        "cpu2_communication_lost": "Comunicación con CPU2 perdida",
        "dsp_communication_lost": "Comunicación con DSP perdida",
        "pv_output_overvoltage": "Sobretensión de salida PV{pv}",
        "pv_output_overcurrent": "Sobrecorriente de salida PV{pv}",
        "pv_input_overvoltage": "Sobretensión de entrada PV{pv}",
        "pv_self_test_fault": "Fallo de autocomprobación PV{pv}",
        "pv_watchdog_reset": "Reinicio del watchdog PV{pv}",
        "pv_bus_overvoltage": "Sobretensión del bus PV{pv}",
        "pv_input_undervoltage": "Tensión de entrada PV{pv} demasiado baja",
        "pv_dsp_fault": "Fallo del DSP de PV{pv}",
        "unknown_inverter": "Alarma del inversor sin identificar ({code})",
        "unknown_controller": "Alarma del controlador sin identificar ({code})",
        "unknown_pv": "Alarma de PV{pv} sin identificar ({code})",
    },
    "it": {
        "grid_undervoltage": "Tensione di rete troppo bassa",
        "dsp_initialization_incomplete": "Inizializzazione DSP incompleta",
        "cpu2_communication_lost": "Comunicazione CPU2 persa",
        "dsp_communication_lost": "Comunicazione DSP persa",
        "pv_output_overvoltage": "Sovratensione di uscita PV{pv}",
        "pv_output_overcurrent": "Sovracorrente di uscita PV{pv}",
        "pv_input_overvoltage": "Sovratensione di ingresso PV{pv}",
        "pv_self_test_fault": "Errore autotest PV{pv}",
        "pv_watchdog_reset": "Reset watchdog PV{pv}",
        "pv_bus_overvoltage": "Sovratensione bus PV{pv}",
        "pv_input_undervoltage": "Tensione di ingresso PV{pv} troppo bassa",
        "pv_dsp_fault": "Guasto DSP PV{pv}",
        "unknown_inverter": "Allarme inverter non identificato ({code})",
        "unknown_controller": "Allarme controller non identificato ({code})",
        "unknown_pv": "Allarme PV{pv} non identificato ({code})",
    },
    "nl": {
        "grid_undervoltage": "Netspanning te laag",
        "dsp_initialization_incomplete": "DSP-initialisatie onvolledig",
        "cpu2_communication_lost": "CPU2-communicatie verloren",
        "dsp_communication_lost": "DSP-communicatie verloren",
        "pv_output_overvoltage": "PV{pv}-uitgangsoverspanning",
        "pv_output_overcurrent": "PV{pv}-uitgangsoverstroom",
        "pv_input_overvoltage": "PV{pv}-ingangsoverspanning",
        "pv_self_test_fault": "PV{pv}-zelftestfout",
        "pv_watchdog_reset": "PV{pv}-watchdogreset",
        "pv_bus_overvoltage": "PV{pv}-busoverspanning",
        "pv_input_undervoltage": "PV{pv}-ingangsspanning te laag",
        "pv_dsp_fault": "PV{pv}-DSP-storing",
        "unknown_inverter": "Niet-geïdentificeerd omvormeralarm ({code})",
        "unknown_controller": "Niet-geïdentificeerd besturingsalarm ({code})",
        "unknown_pv": "Niet-geïdentificeerd PV{pv}-alarm ({code})",
    },
    "pl": {
        "grid_undervoltage": "Zbyt niskie napięcie sieci",
        "dsp_initialization_incomplete": "Inicjalizacja DSP nieukończona",
        "cpu2_communication_lost": "Utrata komunikacji CPU2",
        "dsp_communication_lost": "Utrata komunikacji DSP",
        "pv_output_overvoltage": "Przepięcie wyjściowe PV{pv}",
        "pv_output_overcurrent": "Przetężenie wyjściowe PV{pv}",
        "pv_input_overvoltage": "Przepięcie wejściowe PV{pv}",
        "pv_self_test_fault": "Błąd autotestu PV{pv}",
        "pv_watchdog_reset": "Reset watchdoga PV{pv}",
        "pv_bus_overvoltage": "Przepięcie magistrali PV{pv}",
        "pv_input_undervoltage": "Zbyt niskie napięcie wejściowe PV{pv}",
        "pv_dsp_fault": "Usterka DSP PV{pv}",
        "unknown_inverter": "Nierozpoznany alarm falownika ({code})",
        "unknown_controller": "Nierozpoznany alarm sterownika ({code})",
        "unknown_pv": "Nierozpoznany alarm PV{pv} ({code})",
    },
    "zh-hans": {
        "grid_undervoltage": "电网欠压",
        "dsp_initialization_incomplete": "DSP初始化未完成",
        "cpu2_communication_lost": "CPU2通讯丢失",
        "dsp_communication_lost": "DSP通讯丢失",
        "pv_output_overvoltage": "PV{pv}输出过压",
        "pv_output_overcurrent": "PV{pv}输出过流",
        "pv_input_overvoltage": "PV{pv}输入过压",
        "pv_self_test_fault": "PV{pv}自检故障",
        "pv_watchdog_reset": "PV{pv}看门狗复位",
        "pv_bus_overvoltage": "PV{pv}母线过压",
        "pv_input_undervoltage": "PV{pv}输入电压过低",
        "pv_dsp_fault": "PV{pv} DSP故障",
        "unknown_inverter": "未识别的逆变器报警（{code}）",
        "unknown_controller": "未识别的控制器报警（{code}）",
        "unknown_pv": "未识别的 PV{pv} 报警（{code}）",
    },
}


def _language_texts(language: str) -> dict[str, str]:
    """Return the closest supported language, with English as fallback."""
    normalized = language.replace("_", "-").lower()
    return (
        _TEXTS.get(normalized)
        or _TEXTS.get(normalized.split("-", 1)[0])
        or _TEXTS["en"]
    )


def _alarm_name(definition: AlarmDefinition, language: str) -> str:
    """Return clear local wording for one catalogue position."""
    texts = _language_texts(language)
    if definition.semantic_key is not None:
        template = texts[definition.semantic_key]
    else:
        template = texts[f"unknown_{definition.category}"]
    return template.format(
        code=definition.identifier,
        pv=definition.pv_input if definition.pv_input is not None else "",
    )


def decode_active_alarms(
    measurements: dict[str, Any], language: str
) -> tuple[ActiveAlarm, ...]:
    """Decode active alarm bits without hiding unnamed positions."""
    active: list[ActiveAlarm] = []
    for source in ALARM_SOURCES:
        value = measurements.get(source.key)
        if not isinstance(value, int):
            continue
        for bit in range(16):
            if not value & (1 << bit):
                continue
            definition = ALARM_BY_POSITION[(source.key, bit)]
            active.append(
                ActiveAlarm(
                    identifier=definition.identifier,
                    name=_alarm_name(definition, language),
                    identified=definition.identified,
                )
            )
    return tuple(active)


def alarm_state_attributes(
    measurements: dict[str, Any], language: str
) -> dict[str, Any]:
    """Return compact Home Assistant attributes for active MP3000 alarms."""
    active = decode_active_alarms(measurements, language)
    return {
        "active_alarm_names": [alarm.name for alarm in active],
        "active_alarm_codes": [alarm.identifier for alarm in active],
    }
