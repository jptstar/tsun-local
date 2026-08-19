# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "tsun_local"
KEYS = {
    "grid_qp_voltage_threshold",
    "grid_recovery_rate",
    "grid_overvoltage_10min",
    "grid_overfrequency_reduction_frequency",
    "grid_overfrequency_reduction_coefficient",
    "overtemperature_protection_temperature",
    "grid_start_upper_voltage_limit",
    "grid_start_lower_voltage_limit",
    "grid_start_upper_frequency_limit",
    "grid_start_lower_frequency_limit",
}


class FieldValidationLocalizationTests(unittest.TestCase):
    def test_all_eight_translation_files_have_the_ten_names(self) -> None:
        for filename in (
            "en.json", "fr.json", "de.json", "es.json",
            "it.json", "nl.json", "pl.json", "zh-Hans.json",
        ):
            document = json.loads(
                (INTEGRATION / "translations" / filename).read_text(encoding="utf-8")
            )
            sensors = document["entity"]["sensor"]
            self.assertTrue(KEYS <= set(sensors), filename)
            self.assertTrue(
                all(sensors[key]["name"].strip() for key in KEYS), filename
            )

    def test_source_strings_have_the_same_ten_keys(self) -> None:
        strings = json.loads((INTEGRATION / "strings.json").read_text(encoding="utf-8"))
        self.assertTrue(KEYS <= set(strings["entity"]["sensor"]))

    def test_field_validation_descriptions_use_translation_keys(self) -> None:
        source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        self.assertIn("translation_key=translation_key", source)
        self.assertNotIn("name=name", source)
        for key in KEYS:
            self.assertIn(f'"{key}",\n        "{key}",', source)

    def test_entity_identifiers_remain_stable_english(self) -> None:
        source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        self.assertIn("suggested_object_id=key", source)
        self.assertIn(
            'self._attr_unique_id = f"{logger_sn}_{description.key}"', source
        )

    def test_representative_names_are_localized(self) -> None:
        fr = json.loads(
            (INTEGRATION / "translations" / "fr.json").read_text(encoding="utf-8")
        )["entity"]["sensor"]
        de = json.loads(
            (INTEGRATION / "translations" / "de.json").read_text(encoding="utf-8")
        )["entity"]["sensor"]
        zh = json.loads(
            (INTEGRATION / "translations" / "zh-Hans.json").read_text(encoding="utf-8")
        )["entity"]["sensor"]
        self.assertEqual(
            fr["grid_start_upper_voltage_limit"]["name"],
            "Limite supérieure de tension au démarrage",
        )
        self.assertEqual(
            de["grid_qp_voltage_threshold"]["name"], "QP-Spannungsschwelle"
        )
        self.assertEqual(
            zh["grid_overfrequency_reduction_coefficient"]["name"], "过频降额系数"
        )


if __name__ == "__main__":
    unittest.main()
