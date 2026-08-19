# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Localized display names for MP3000 field-validation diagnostics.

The entity keys, suggested object IDs and unique IDs intentionally remain stable
English identifiers. Only the human-readable Home Assistant display name is
localized.
"""

from __future__ import annotations

from dataclasses import replace


FIELD_VALIDATION_NAMES: dict[str, dict[str, str]] = {
    "en": {
        "grid_qp_voltage_threshold": "QP voltage threshold",
        "grid_recovery_rate": "Grid recovery time",
        "grid_overvoltage_10min": "10-minute grid overvoltage protection",
        "grid_overfrequency_reduction_frequency": "Overfrequency reduction value",
        "grid_overfrequency_reduction_coefficient": "Overfrequency reduction coefficient",
        "overtemperature_protection_temperature": "Overtemperature protection threshold",
        "grid_start_upper_voltage_limit": "Upper startup voltage limit",
        "grid_start_lower_voltage_limit": "Lower startup voltage limit",
        "grid_start_upper_frequency_limit": "Upper startup frequency limit",
        "grid_start_lower_frequency_limit": "Lower startup frequency limit",
    },
    "fr": {
        "grid_qp_voltage_threshold": "Seuil de tension QP",
        "grid_recovery_rate": "Temps de récupération réseau",
        "grid_overvoltage_10min": "Protection surtension réseau 10 minutes",
        "grid_overfrequency_reduction_frequency": "Valeur de réduction de surfréquence",
        "grid_overfrequency_reduction_coefficient": "Coefficient de réduction de surfréquence",
        "overtemperature_protection_temperature": "Seuil de protection contre la surtempérature",
        "grid_start_upper_voltage_limit": "Limite supérieure de tension au démarrage",
        "grid_start_lower_voltage_limit": "Limite inférieure de tension au démarrage",
        "grid_start_upper_frequency_limit": "Limite supérieure de fréquence au démarrage",
        "grid_start_lower_frequency_limit": "Limite inférieure de fréquence au démarrage",
    },
    "de": {
        "grid_qp_voltage_threshold": "QP-Spannungsschwelle",
        "grid_recovery_rate": "Netz-Wiederherstellungszeit",
        "grid_overvoltage_10min": "10-Minuten-Netzüberspannungsschutz",
        "grid_overfrequency_reduction_frequency": "Wert der Überfrequenz-Leistungsreduzierung",
        "grid_overfrequency_reduction_coefficient": "Koeffizient der Überfrequenz-Leistungsreduzierung",
        "overtemperature_protection_temperature": "Übertemperatur-Schutzschwelle",
        "grid_start_upper_voltage_limit": "Obere Startspannungsgrenze",
        "grid_start_lower_voltage_limit": "Untere Startspannungsgrenze",
        "grid_start_upper_frequency_limit": "Obere Startfrequenzgrenze",
        "grid_start_lower_frequency_limit": "Untere Startfrequenzgrenze",
    },
    "es": {
        "grid_qp_voltage_threshold": "Umbral de tensión QP",
        "grid_recovery_rate": "Tiempo de recuperación de red",
        "grid_overvoltage_10min": "Protección de sobretensión de red de 10 minutos",
        "grid_overfrequency_reduction_frequency": "Valor de reducción por sobrefrecuencia",
        "grid_overfrequency_reduction_coefficient": "Coeficiente de reducción por sobrefrecuencia",
        "overtemperature_protection_temperature": "Umbral de protección por sobretemperatura",
        "grid_start_upper_voltage_limit": "Límite superior de tensión de arranque",
        "grid_start_lower_voltage_limit": "Límite inferior de tensión de arranque",
        "grid_start_upper_frequency_limit": "Límite superior de frecuencia de arranque",
        "grid_start_lower_frequency_limit": "Límite inferior de frecuencia de arranque",
    },
    "it": {
        "grid_qp_voltage_threshold": "Soglia tensione QP",
        "grid_recovery_rate": "Tempo di ripristino rete",
        "grid_overvoltage_10min": "Protezione sovratensione rete 10 minuti",
        "grid_overfrequency_reduction_frequency": "Valore riduzione sovrafrequenza",
        "grid_overfrequency_reduction_coefficient": "Coefficiente riduzione sovrafrequenza",
        "overtemperature_protection_temperature": "Soglia protezione sovratemperatura",
        "grid_start_upper_voltage_limit": "Limite superiore tensione di avvio",
        "grid_start_lower_voltage_limit": "Limite inferiore tensione di avvio",
        "grid_start_upper_frequency_limit": "Limite superiore frequenza di avvio",
        "grid_start_lower_frequency_limit": "Limite inferiore frequenza di avvio",
    },
    "nl": {
        "grid_qp_voltage_threshold": "QP-spanningsdrempel",
        "grid_recovery_rate": "Nethersteltijd",
        "grid_overvoltage_10min": "10-minuten-netoverspanningsbeveiliging",
        "grid_overfrequency_reduction_frequency": "Waarde overfrequentiereductie",
        "grid_overfrequency_reduction_coefficient": "Coëfficiënt overfrequentiereductie",
        "overtemperature_protection_temperature": "Drempel overtemperatuurbeveiliging",
        "grid_start_upper_voltage_limit": "Bovengrens startspanning",
        "grid_start_lower_voltage_limit": "Ondergrens startspanning",
        "grid_start_upper_frequency_limit": "Bovengrens startfrequentie",
        "grid_start_lower_frequency_limit": "Ondergrens startfrequentie",
    },
    "pl": {
        "grid_qp_voltage_threshold": "Próg napięcia QP",
        "grid_recovery_rate": "Czas przywracania sieci",
        "grid_overvoltage_10min": "10-minutowe zabezpieczenie nadnapięciowe sieci",
        "grid_overfrequency_reduction_frequency": "Wartość redukcji przy nadczęstotliwości",
        "grid_overfrequency_reduction_coefficient": "Współczynnik redukcji przy nadczęstotliwości",
        "overtemperature_protection_temperature": "Próg zabezpieczenia nadtemperaturowego",
        "grid_start_upper_voltage_limit": "Górna granica napięcia rozruchowego",
        "grid_start_lower_voltage_limit": "Dolna granica napięcia rozruchowego",
        "grid_start_upper_frequency_limit": "Górna granica częstotliwości rozruchowej",
        "grid_start_lower_frequency_limit": "Dolna granica częstotliwości rozruchowej",
    },
    "zh-hans": {
        "grid_qp_voltage_threshold": "QP 电压阈值",
        "grid_recovery_rate": "电网恢复时间",
        "grid_overvoltage_10min": "10 分钟电网过压保护",
        "grid_overfrequency_reduction_frequency": "过频降额值",
        "grid_overfrequency_reduction_coefficient": "过频降额系数",
        "overtemperature_protection_temperature": "过温保护阈值",
        "grid_start_upper_voltage_limit": "启动电压上限",
        "grid_start_lower_voltage_limit": "启动电压下限",
        "grid_start_upper_frequency_limit": "启动频率上限",
        "grid_start_lower_frequency_limit": "启动频率下限",
    },
}

FIELD_VALIDATION_KEYS = frozenset(FIELD_VALIDATION_NAMES["en"])


def field_validation_name(key: str, language: str) -> str:
    """Return a localized display name with English as the safe fallback."""
    normalized = language.replace("_", "-").lower()
    names = (
        FIELD_VALIDATION_NAMES.get(normalized)
        or FIELD_VALIDATION_NAMES.get(normalized.split("-", 1)[0])
        or FIELD_VALIDATION_NAMES["en"]
    )
    return names.get(key, FIELD_VALIDATION_NAMES["en"].get(key, key))


def apply_field_validation_names(language: str) -> None:
    """Apply localized names without changing entity identifiers."""
    # Import lazily to avoid a circular import while the integration package is
    # initialized. async_setup_entry calls this before forwarding sensor setup.
    from . import sensor as sensor_platform

    sensor_platform.SENSORS = tuple(
        replace(
            description,
            name=field_validation_name(description.key, language),
        )
        if description.key in FIELD_VALIDATION_KEYS
        else description
        for description in sensor_platform.SENSORS
    )
