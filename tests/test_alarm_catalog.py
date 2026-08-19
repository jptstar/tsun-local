# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify the complete independent MP3000 alarm catalogue."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parents[1]
CATALOGUE_PATH = ROOT / "custom_components" / "tsun_local" / "alarm_catalog.py"
SPEC = importlib.util.spec_from_file_location(
    "tsun_local_alarm_catalog_tests", CATALOGUE_PATH
)
assert SPEC is not None and SPEC.loader is not None
CATALOGUE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CATALOGUE
SPEC.loader.exec_module(CATALOGUE)


class AlarmCatalogueTests(unittest.TestCase):
    """Keep all positions active while limiting names to verified meanings."""

    def test_catalogues_all_fourteen_words_and_224_positions(self) -> None:
        definitions = CATALOGUE.ALARM_CATALOGUE
        self.assertEqual(len(CATALOGUE.ALARM_SOURCES), 14)
        self.assertEqual(len(definitions), 224)
        self.assertEqual(len({item.identifier for item in definitions}), 224)
        self.assertEqual(
            len({(item.source_key, item.bit) for item in definitions}), 224
        )
        self.assertEqual(definitions[0].identifier, "A001")
        self.assertEqual(definitions[-1].identifier, "A224")

    def test_all_224_active_positions_are_reported(self) -> None:
        measurements = {
            source.key: 0xFFFF for source in CATALOGUE.ALARM_SOURCES
        }
        active = CATALOGUE.decode_active_alarms(measurements, "fr")

        self.assertEqual(len(active), 224)
        self.assertEqual(sum(alarm.identified for alarm in active), 12)
        self.assertEqual(sum(not alarm.identified for alarm in active), 212)

    def test_only_twelve_positions_have_confirmed_names(self) -> None:
        identified = [
            definition
            for definition in CATALOGUE.ALARM_CATALOGUE
            if definition.identified
        ]
        self.assertEqual(len(identified), 12)
        self.assertEqual({definition.bit for definition in identified}, {8, 10})

    def test_validated_positions_have_stable_expected_codes(self) -> None:
        expected = {
            (f"pv{number}_alarm_raw", bit): f"A{129 + (number - 1) * 16 + bit:03d}"
            for number in range(1, 7)
            for bit in (8, 10)
        }
        actual = {
            (definition.source_key, definition.bit): definition.identifier
            for definition in CATALOGUE.ALARM_CATALOGUE
            if definition.identified
        }
        self.assertEqual(actual, expected)

    def test_observed_8192_position_has_stable_neutral_code(self) -> None:
        active = CATALOGUE.decode_active_alarms(
            {"alarm_global_1_raw": 0x2000}, "en"
        )
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].identifier, "A030")
        self.assertFalse(active[0].identified)

    def test_french_names_and_neutral_pending_fallback(self) -> None:
        active = CATALOGUE.decode_active_alarms(
            {
                "alarm_global_0_raw": 1 << 2,
                "pv1_alarm_raw": (1 << 8) | (1 << 10),
            },
            "fr-FR",
        )
        self.assertEqual(
            [alarm.name for alarm in active],
            [
                "Alarme onduleur non identifiée",
                "Tension d’entrée PV1 trop faible",
                "Défaut du DSP PV1",
            ],
        )

    def test_active_alarm_state_is_localized_and_code_free(self) -> None:
        self.assertEqual(
            CATALOGUE.active_alarm_state({"pv1_alarm_raw": 1 << 10}, "fr"),
            "Défaut du DSP PV1",
        )
        self.assertEqual(CATALOGUE.active_alarm_state({}, "fr"), "Aucune alarme active")
        unknown = CATALOGUE.active_alarm_state(
            {"alarm_global_0_raw": 1 << 2}, "fr"
        )
        self.assertEqual(unknown, "Alarme onduleur non identifiée")
        self.assertNotIn("A003", unknown)

    def test_active_alarm_state_is_bounded_for_many_alarms(self) -> None:
        measurements = {
            source.key: 0xFFFF for source in CATALOGUE.ALARM_SOURCES
        }
        state = CATALOGUE.active_alarm_state(measurements, "fr")
        self.assertLessEqual(len(state), 255)

    def test_all_supported_languages_have_complete_wording(self) -> None:
        for language in ("en", "fr", "de", "es", "it", "nl", "pl", "zh-Hans"):
            active = CATALOGUE.decode_active_alarms(
                {"pv6_alarm_raw": (1 << 8) | (1 << 10) | (1 << 15)},
                language,
            )
            self.assertEqual(len(active), 3)
            self.assertTrue(all(alarm.name.strip() for alarm in active))
            self.assertTrue(all("{" not in alarm.name for alarm in active))

    def test_all_language_catalogues_have_the_same_keys(self) -> None:
        expected = set(CATALOGUE._TEXTS["en"])
        self.assertEqual(set(CATALOGUE._TEXTS), {
            "en", "fr", "de", "es", "it", "nl", "pl", "zh-hans"
        })
        for language, texts in CATALOGUE._TEXTS.items():
            self.assertEqual(set(texts), expected, language)

    def test_home_assistant_attributes_only_expose_active_names_and_codes(self) -> None:
        attributes = CATALOGUE.alarm_state_attributes(
            {"pv1_alarm_raw": 1 << 8}, "en"
        )
        self.assertEqual(
            set(attributes), {"active_alarm_names", "active_alarm_codes"}
        )


if __name__ == "__main__":
    unittest.main()
