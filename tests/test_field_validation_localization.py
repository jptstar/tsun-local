# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Regression tests for localized MP3000 beta diagnostic names."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
MODULE_PATH = (
    ROOT
    / "custom_components"
    / "tsun_local"
    / "field_validation_localization.py"
)
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_field_validation_localization_tests", MODULE_PATH
)
assert SPEC is not None and SPEC.loader is not None
LOCALIZATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = LOCALIZATION
SPEC.loader.exec_module(LOCALIZATION)


class FieldValidationLocalizationTests(unittest.TestCase):
    """Keep localized names complete without changing entity identifiers."""

    def test_all_eight_languages_cover_the_same_ten_keys(self) -> None:
        names = LOCALIZATION.FIELD_VALIDATION_NAMES
        self.assertEqual(
            set(names),
            {"en", "fr", "de", "es", "it", "nl", "pl", "zh-hans"},
        )
        expected = set(names["en"])
        self.assertEqual(len(expected), 10)
        self.assertEqual(expected, set(LOCALIZATION.FIELD_VALIDATION_KEYS))
        for language, translated in names.items():
            self.assertEqual(set(translated), expected, language)
            self.assertTrue(all(value.strip() for value in translated.values()))

    def test_language_variants_and_fallback(self) -> None:
        self.assertEqual(
            LOCALIZATION.field_validation_name(
                "grid_start_upper_voltage_limit", "fr-FR"
            ),
            "Limite supérieure de tension au démarrage",
        )
        self.assertEqual(
            LOCALIZATION.field_validation_name(
                "grid_qp_voltage_threshold", "de-DE"
            ),
            "QP-Spannungsschwelle",
        )
        self.assertEqual(
            LOCALIZATION.field_validation_name(
                "grid_overfrequency_reduction_coefficient", "zh-Hans"
            ),
            "过频降额系数",
        )
        self.assertEqual(
            LOCALIZATION.field_validation_name(
                "grid_qp_voltage_threshold", "unsupported"
            ),
            "QP voltage threshold",
        )

    def test_entity_identifiers_stay_english_and_stable(self) -> None:
        sensor_source = (
            ROOT / "custom_components" / "tsun_local" / "sensor.py"
        ).read_text(encoding="utf-8")
        init_source = (
            ROOT / "custom_components" / "tsun_local" / "__init__.py"
        ).read_text(encoding="utf-8")
        self.assertIn("suggested_object_id=key", sensor_source)
        self.assertIn(
            'self._attr_unique_id = f"{logger_sn}_{description.key}"',
            sensor_source,
        )
        self.assertIn(
            "apply_field_validation_names(hass.config.language)", init_source
        )


if __name__ == "__main__":
    unittest.main()
