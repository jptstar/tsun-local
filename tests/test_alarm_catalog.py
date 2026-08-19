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
    """Keep all positions active while tracking physical validation separately."""

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

    def test_csv_names_and_physical_validation_are_separate(self) -> None:
        definitions = CATALOGUE.ALARM_CATALOGUE
        named = [item for item in definitions if item.semantic_key is not None]
        validated = [item for item in definitions if item.validated]

        self.assertEqual(len(named), 52)
        self.assertEqual(len(validated), 12)
        self.assertTrue(all(item.semantic_key is not None for item in validated))
        self.assertEqual(
            {(item.pv_input, item.bit) for item in validated},
            {(pv, bit) for pv in range(1, 7) for bit in (8, 10)},
        )

    def test_csv_global_and_controller_candidate_positions(self) -> None:
        expected = {
            ("alarm_global_0_raw", 0): ("A001", "grid_undervoltage"),
            (
                "alarm_secondary_0_raw",
                0,
            ): ("A065", "dsp_initialization_incomplete"),
            (
                "alarm_secondary_0_raw",
                4,
            ): ("A069", "cpu2_communication_lost"),
            (
                "alarm_secondary_0_raw",
                6,
            ): ("A071", "dsp_communication_lost"),
        }
        for position, (identifier, semantic_key) in expected.items():
            definition = CATALOGUE.ALARM_BY_POSITION[position]
            self.assertEqual(definition.identifier, identifier)
            self.assertEqual(definition.semantic_key, semantic_key)
            self.assertFalse(definition.validated)

    def test_csv_pv_sequence_is_applied_to_all_six_inputs(self) -> None:
        expected = {
            1: "pv_output_overvoltage",
            2: "pv_output_overcurrent",
            3: "pv_input_overvoltage",
            5: "pv_self_test_fault",
            6: "pv_watchdog_reset",
            7: "pv_bus_overvoltage",
            8: "pv_input_undervoltage",
            10: "pv_dsp_fault",
        }
        for pv in range(1, 7):
            for bit, semantic_key in expected.items():
                definition = CATALOGUE.ALARM_BY_POSITION[
                    (f"pv{pv}_alarm_raw", bit)
                ]
                self.assertEqual(definition.semantic_key, semantic_key)

    def test_existing_validated_positions_keep_stable_codes(self) -> None:
        expected = {
            (f"pv{number}_alarm_raw", bit): f"A{129 + (number - 1) * 16 + bit:03d}"
            for number in range(1, 7)
            for bit in (8, 10)
        }
        actual = {
            (definition.source_key, definition.bit): definition.identifier
            for definition in CATALOGUE.ALARM_CATALOGUE
            if definition.validated
        }
        self.assertEqual(actual, expected)

    def test_observed_8192_position_remains_neutral(self) -> None:
        active = CATALOGUE.decode_active_alarms(
            {"alarm_global_1_raw": 0x2000}, "en"
        )
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].identifier, "A030")
        self.assertEqual(active[0].name, "Unidentified inverter alarm (A030)")
        self.assertFalse(active[0].identified)

    def test_french_csv_named_alarm_is_shown_without_validation_marker(self) -> None:
        active = CATALOGUE.decode_active_alarms(
            {
                "alarm_global_0_raw": 1,
                "alarm_secondary_0_raw": (1 << 4) | (1 << 6),
                "pv3_alarm_raw": (1 << 3) | (1 << 8) | (1 << 10),
            },
            "fr-FR",
        )
        self.assertEqual(
            [alarm.name for alarm in active],
            [
                "Sous-tension du réseau électrique",
                "Communication CPU2 perdue",
                "Communication DSP perdue",
                "Surtension d’entrée PV3",
                "Tension d’entrée PV3 trop faible",
                "Défaut du DSP PV3",
            ],
        )

    def test_truly_unnamed_positions_keep_neutral_fallback(self) -> None:
        active = CATALOGUE.decode_active_alarms(
            {"pv1_alarm_raw": 1 << 9}, "fr"
        )
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].identifier, "A138")
        self.assertEqual(active[0].name, "Alarme PV1 non identifiée (A138)")

    def test_all_supported_languages_have_complete_wording(self) -> None:
        measurements = {
            "alarm_global_0_raw": 1,
            "alarm_secondary_0_raw": 1 | (1 << 4) | (1 << 6),
            "pv6_alarm_raw": sum(1 << bit for bit in (1, 2, 3, 5, 6, 7, 8, 10, 15)),
        }
        for language in ("en", "fr", "de", "es", "it", "nl", "pl", "zh-Hans"):
            active = CATALOGUE.decode_active_alarms(measurements, language)
            self.assertEqual(len(active), 13)
            self.assertTrue(all(alarm.name.strip() for alarm in active))
            self.assertTrue(all("{" not in alarm.name for alarm in active))

    def test_all_language_catalogues_have_the_same_keys(self) -> None:
        expected = set(CATALOGUE._TEXTS["en"])
        self.assertEqual(
            set(CATALOGUE._TEXTS),
            {"en", "fr", "de", "es", "it", "nl", "pl", "zh-hans"},
        )
        for language, texts in CATALOGUE._TEXTS.items():
            self.assertEqual(set(texts), expected, language)

    def test_home_assistant_attributes_only_expose_names_and_codes(self) -> None:
        attributes = CATALOGUE.alarm_state_attributes(
            {"pv3_alarm_raw": 1 << 3}, "en"
        )
        self.assertEqual(
            set(attributes), {"active_alarm_names", "active_alarm_codes"}
        )
        self.assertEqual(
            attributes["active_alarm_names"], ["PV3 input overvoltage"]
        )


if __name__ == "__main__":
    unittest.main()
