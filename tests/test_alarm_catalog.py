# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Verify the protocol-aware TSUN Local alarm catalogues."""

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
    """Keep complete per-protocol positions and stable public alarm codes."""

    def test_catalogue_sizes_and_public_code_ranges(self) -> None:
        self.assertEqual(len(CATALOGUE.ALARM_CATALOGUES["1511"]), 224)
        self.assertEqual(len(CATALOGUE.ALARM_CATALOGUES["02b0"]), 64)
        self.assertEqual(len(CATALOGUE.ALARM_CATALOGUES["1097"]), 64)
        self.assertEqual(CATALOGUE.ALARM_CATALOGUES["1511"][0].identifier, "1511-A001")
        self.assertEqual(CATALOGUE.ALARM_CATALOGUES["1511"][-1].identifier, "1511-A224")
        self.assertEqual(CATALOGUE.ALARM_CATALOGUES["02b0"][0].identifier, "02B0-A001")
        self.assertEqual(CATALOGUE.ALARM_CATALOGUES["02b0"][-1].identifier, "02B0-A064")
        self.assertEqual(CATALOGUE.ALARM_CATALOGUES["1097"][0].identifier, "1097-A001")
        self.assertEqual(CATALOGUE.ALARM_CATALOGUES["1097"][-1].identifier, "1097-A064")

    def test_backwards_aliases_still_reference_1511(self) -> None:
        self.assertIs(CATALOGUE.ALARM_SOURCES, CATALOGUE.ALARM_SOURCES_BY_PROTOCOL["1511"])
        self.assertIs(CATALOGUE.ALARM_CATALOGUE, CATALOGUE.ALARM_CATALOGUES["1511"])
        self.assertEqual(len(CATALOGUE.ALARM_BY_POSITION), 224)

    def test_all_1511_active_positions_are_reported(self) -> None:
        measurements = {
            source.key: 0xFFFF
            for source in CATALOGUE.ALARM_SOURCES_BY_PROTOCOL["1511"]
        }
        active = CATALOGUE.decode_active_alarms(measurements, "fr", "1511")
        self.assertEqual(len(active), 224)
        self.assertEqual(sum(alarm.identified for alarm in active), 12)
        self.assertEqual(sum(not alarm.identified for alarm in active), 212)

    def test_1511_known_and_unknown_names_always_include_code(self) -> None:
        active = CATALOGUE.decode_active_alarms(
            {
                "alarm_global_0_raw": 1 << 2,
                "pv1_alarm_raw": 1 << 8,
            },
            "fr-FR",
            "1511",
        )
        self.assertEqual(
            [alarm.name for alarm in active],
            [
                "Alarme onduleur non identifiée (1511-A003)",
                "Tension d’entrée PV1 trop faible (1511-A137)",
            ],
        )

    def test_02b0_known_and_unknown_alarm_positions(self) -> None:
        active = CATALOGUE.decode_active_alarms(
            {
                "alarm_code_1_raw": (1 << 13) | (1 << 5),
                "alarm_code_2_raw": 1 << 0,
                "alarm_code_3_raw": 0,
                "alarm_code_4_raw": 0,
            },
            "fr",
            "02b0",
        )
        self.assertEqual(
            [alarm.name for alarm in active],
            [
                "Alarme onduleur non identifiée (02B0-A006)",
                "Sous-tension réseau (02B0-A014)",
                "Surtension PV (02B0-A017)",
            ],
        )

    def test_1097_uses_its_own_stable_positions(self) -> None:
        active = CATALOGUE.decode_active_alarms(
            {
                "_alarm_protocol": "1097",
                "alarm_code_1_raw": 1 << 3,
                "alarm_code_2_raw": 0,
                "alarm_code_3_raw": 1 << 8,
                "alarm_code_4_raw": 0,
            },
            "fr",
        )
        self.assertEqual(
            [alarm.name for alarm in active],
            [
                "Surchauffe (1097-A004)",
                "Alarme onduleur non identifiée (1097-A041)",
            ],
        )

    def test_active_alarm_state_is_localized_and_bounded(self) -> None:
        self.assertEqual(
            CATALOGUE.active_alarm_state(
                {"pv1_alarm_raw": 1 << 10}, "fr", "1511"
            ),
            "Défaut du DSP PV1 (1511-A139)",
        )
        self.assertEqual(
            CATALOGUE.active_alarm_state({}, "fr", "1511"),
            "Aucune alarme active",
        )
        measurements = {
            source.key: 0xFFFF
            for source in CATALOGUE.ALARM_SOURCES_BY_PROTOCOL["1511"]
        }
        self.assertLessEqual(
            len(CATALOGUE.active_alarm_state(measurements, "fr", "1511")),
            255,
        )

    def test_all_supported_languages_have_complete_wording(self) -> None:
        for language in ("en", "fr", "de", "es", "it", "nl", "pl", "zh-Hans"):
            active = CATALOGUE.decode_active_alarms(
                {
                    "alarm_code_1_raw": (1 << 2) | (1 << 13),
                    "alarm_code_2_raw": 1 << 1,
                    "alarm_code_3_raw": 1 << 8,
                    "alarm_code_4_raw": 0,
                },
                language,
                "02b0",
            )
            self.assertEqual(len(active), 4)
            self.assertTrue(all(alarm.name.strip() for alarm in active))
            self.assertTrue(all("{" not in alarm.name for alarm in active))
            self.assertTrue(all("(02B0-A" in alarm.name for alarm in active))

    def test_all_language_catalogues_have_the_same_keys(self) -> None:
        expected = set(CATALOGUE._TEXTS["en"])
        self.assertEqual(
            set(CATALOGUE._TEXTS),
            {"en", "fr", "de", "es", "it", "nl", "pl", "zh-hans"},
        )
        for language, texts in CATALOGUE._TEXTS.items():
            self.assertEqual(set(texts), expected, language)

    def test_home_assistant_attributes_expose_names_and_public_codes(self) -> None:
        attributes = CATALOGUE.alarm_state_attributes(
            {
                "_alarm_protocol": "02b0",
                "alarm_code_1_raw": 1 << 13,
                "alarm_code_2_raw": 0,
                "alarm_code_3_raw": 0,
                "alarm_code_4_raw": 0,
            },
            "en",
        )
        self.assertEqual(
            attributes,
            {
                "active_alarm_names": ["Grid undervoltage (02B0-A014)"],
                "active_alarm_codes": ["02B0-A014"],
            },
        )


if __name__ == "__main__":
    unittest.main()
