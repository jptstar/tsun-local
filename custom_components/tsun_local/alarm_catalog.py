# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Independent MP3000 alarm catalogue and local decoder.

All fourteen 16-bit words have a stable local position. Functional wording is
assigned only to positions confirmed on hardware; every other position keeps
an explicit, neutral local identifier until physical validation is available.
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

    @property
    def identified(self) -> bool:
        """Return whether this position has a validated functional meaning."""
        return self.semantic_key is not None


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

# These twelve mappings are supported by direct physical observations.
_IDENTIFIED_POSITIONS: dict[tuple[str, int], str] = {
    **{
        (f"pv{number}_alarm_raw", 8): "pv_input_undervoltage"
        for number in range(1, 7)
    },
    **{
        (f"pv{number}_alarm_raw", 10): "pv_dsp_fault"
        for number in range(1, 7)
    },
}

def _build_catalogue() -> tuple[AlarmDefinition, ...]:
    """Build the complete 14 x 16 catalogue with opaque stable identifiers."""
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
                    semantic_key=_IDENTIFIED_POSITIONS.get(source_position),
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
        "pv_input_undervoltage": "PV{pv} input voltage too low",
        "pv_dsp_fault": "PV{pv} DSP fault",
        "unknown_inverter": "Unidentified inverter alarm ({code})",
        "unknown_controller": "Unidentified controller alarm ({code})",
        "unknown_pv": "Unidentified PV{pv} alarm ({code})",
    },
    "fr": {
        "pv_input_undervoltage": "Tension d’entrée PV{pv} trop faible",
        "pv_dsp_fault": "Défaut du DSP PV{pv}",
        "unknown_inverter": "Alarme onduleur non identifiée ({code})",
        "unknown_controller": "Alarme contrôleur non identifiée ({code})",
        "unknown_pv": "Alarme PV{pv} non identifiée ({code})",
    },
    "de": {
        "pv_input_undervoltage": "PV{pv}-Eingangsspannung zu niedrig",
        "pv_dsp_fault": "PV{pv}-DSP-Fehler",
        "unknown_inverter": "Nicht identifizierter Wechselrichteralarm ({code})",
        "unknown_controller": "Nicht identifizierter Steuerungsalarm ({code})",
        "unknown_pv": "Nicht identifizierter PV{pv}-Alarm ({code})",
    },
    "es": {
        "pv_input_undervoltage": "Tensión de entrada PV{pv} demasiado baja",
        "pv_dsp_fault": "Fallo del DSP de PV{pv}",
        "unknown_inverter": "Alarma del inversor sin identificar ({code})",
        "unknown_controller": "Alarma del controlador sin identificar ({code})",
        "unknown_pv": "Alarma de PV{pv} sin identificar ({code})",
    },
    "it": {
        "pv_input_undervoltage": "Tensione di ingresso PV{pv} troppo bassa",
        "pv_dsp_fault": "Guasto DSP PV{pv}",
        "unknown_inverter": "Allarme inverter non identificato ({code})",
        "unknown_controller": "Allarme controller non identificato ({code})",
        "unknown_pv": "Allarme PV{pv} non identificato ({code})",
    },
    "nl": {
        "pv_input_undervoltage": "PV{pv}-ingangsspanning te laag",
        "pv_dsp_fault": "PV{pv}-DSP-storing",
        "unknown_inverter": "Niet-geïdentificeerd omvormeralarm ({code})",
        "unknown_controller": "Niet-geïdentificeerd besturingsalarm ({code})",
        "unknown_pv": "Niet-geïdentificeerd PV{pv}-alarm ({code})",
    },
    "pl": {
        "pv_input_undervoltage": "Zbyt niskie napięcie wejściowe PV{pv}",
        "pv_dsp_fault": "Usterka DSP PV{pv}",
        "unknown_inverter": "Nierozpoznany alarm falownika ({code})",
        "unknown_controller": "Nierozpoznany alarm sterownika ({code})",
        "unknown_pv": "Nierozpoznany alarm PV{pv} ({code})",
    },
    "zh-hans": {
        "pv_input_undervoltage": "PV{pv} 输入电压过低",
        "pv_dsp_fault": "PV{pv} DSP 故障",
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
    """Decode active alarm bits without guessing unknown meanings."""
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
