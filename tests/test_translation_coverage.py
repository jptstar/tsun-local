from __future__ import annotations

import ast
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
COMPONENT = ROOT / "custom_components" / "tsun_local"
TRANSLATIONS = COMPONENT / "translations"
SUPPORTED = {"en.json", "fr.json", "de.json", "es.json", "it.json", "nl.json", "pl.json", "zh-Hans.json"}


class TranslationCoverageTests(unittest.TestCase):
    def test_all_supported_translation_files_exist(self) -> None:
        self.assertEqual({path.name for path in TRANSLATIONS.glob("*.json")}, SUPPORTED)

    def test_every_entity_key_has_a_name_in_every_language(self) -> None:
        canonical = json.loads((COMPONENT / "strings.json").read_text(encoding="utf-8"))
        expected = canonical["entity"]
        for path in sorted(TRANSLATIONS.glob("*.json")):
            translated = json.loads(path.read_text(encoding="utf-8"))["entity"]
            for platform, definitions in expected.items():
                self.assertIn(platform, translated, f"{path.name}: missing {platform}")
                for key in definitions:
                    self.assertIn(key, translated[platform], f"{path.name}: missing {platform}.{key}")
                    name = translated[platform][key].get("name")
                    self.assertIsInstance(name, str, f"{path.name}: missing name for {platform}.{key}")
                    self.assertTrue(name.strip(), f"{path.name}: empty name for {platform}.{key}")

    def test_active_alarm_names_entity_is_declared(self) -> None:
        source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
        self.assertIn('key="active_alarm_names"', source)
        self.assertIn('translation_key="active_alarm_names"', source)
        self.assertIn('suggested_object_id="active_alarm_names"', source)

    def test_removed_candidate_is_not_exposed(self) -> None:
        key = "output_coefficient_candidate"
        self.assertNotIn(key, (COMPONENT / "sensor.py").read_text(encoding="utf-8"))
        self.assertNotIn(key, (COMPONENT / "protocols" / "protocol_1511.py").read_text(encoding="utf-8"))
        for path in [COMPONENT / "strings.json", *TRANSLATIONS.glob("*.json")]:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn(key, data.get("entity", {}).get("sensor", {}), path.name)

    def test_alarm_catalog_has_all_eight_languages_and_same_text_keys(self) -> None:
        tree = ast.parse((COMPONENT / "alarm_catalog.py").read_text(encoding="utf-8"))
        texts = None
        for node in tree.body:
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "_TEXTS":
                texts = ast.literal_eval(node.value)
                break
        self.assertIsNotNone(texts)
        assert texts is not None
        self.assertEqual(set(texts), {"en", "fr", "de", "es", "it", "nl", "pl", "zh-hans"})
        expected = set(texts["en"])
        for language, values in texts.items():
            self.assertEqual(set(values), expected, language)
            self.assertTrue(all(isinstance(value, str) and value.strip() for value in values.values()))


if __name__ == "__main__":
    unittest.main()
