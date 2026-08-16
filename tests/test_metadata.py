# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Project metadata, privacy, and translation consistency tests."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "tsun_local"


def _load_json(path: Path) -> dict:
    """Load one project JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def _leaf_paths(value: object, prefix: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    """Return every translatable leaf path in a nested JSON object."""
    if not isinstance(value, dict):
        return {prefix}
    paths: set[tuple[str, ...]] = set()
    for key, nested_value in value.items():
        paths.update(_leaf_paths(nested_value, (*prefix, key)))
    return paths


class MetadataTests(unittest.TestCase):
    """Keep release metadata and public files synchronized."""

    def test_manifest_version_has_matching_changelog_entry(self) -> None:
        manifest = _load_json(INTEGRATION / "manifest.json")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## [{manifest['version']}]", changelog)

    def test_translation_keys_match_strings(self) -> None:
        strings = _load_json(INTEGRATION / "strings.json")
        expected = _leaf_paths(strings) - {("title",)}
        for path in sorted((INTEGRATION / "translations").glob("*.json")):
            translated = _load_json(path)["entity"]
            translated_document = _load_json(path)
            self.assertEqual(
                _leaf_paths(translated_document),
                expected,
                f"translation keys differ in {path.name}",
            )
            self.assertEqual(set(translated), {"sensor", "binary_sensor", "button"})

    def test_connectivity_binary_sensor_has_an_explicit_localized_name(self) -> None:
        expected_names = {
            "de.json": "Mikrowechselrichter online",
            "en.json": "Micro-inverter online",
            "es.json": "Microinversor en línea",
            "fr.json": "Micro-onduleur en ligne",
            "it.json": "Microinverter online",
            "nl.json": "Micro-omvormer online",
            "pl.json": "Mikrofalownik online",
            "zh-Hans.json": "微型逆变器在线",
        }
        strings = _load_json(INTEGRATION / "strings.json")
        self.assertEqual(
            strings["entity"]["binary_sensor"]["communication_online"]["name"],
            "Micro-inverter online",
        )
        for filename, expected_name in expected_names.items():
            translated = _load_json(INTEGRATION / "translations" / filename)
            self.assertEqual(
                translated["entity"]["binary_sensor"]["communication_online"][
                    "name"
                ],
                expected_name,
            )

    def test_device_identifiers_are_clear_and_mac_is_not_a_link(self) -> None:
        """Keep both SN values explicit and the MAC diagnostic non-clickable."""
        strings = _load_json(INTEGRATION / "strings.json")
        sensors = strings["entity"]["sensor"]
        self.assertEqual(sensors["label_serial_number"]["name"], "SN")
        self.assertEqual(
            sensors["inverter_serial_number"]["name"],
            "Micro-inverter SN",
        )
        sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        self.assertNotIn("CONNECTION_NETWORK_MAC", sensor_source)
        self.assertNotIn("connections=", sensor_source)

    def test_raw_logger_profile_is_device_info_only(self) -> None:
        """Keep the raw profile out of entities and clean the beta.4 orphan."""
        strings = _load_json(INTEGRATION / "strings.json")
        self.assertNotIn(
            "logger_raw_profile", strings["entity"]["sensor"]
        )
        init_source = (INTEGRATION / "__init__.py").read_text(encoding="utf-8")
        self.assertIn(
            'legacy_unique_id = f"{logger_sn}_logger_raw_profile"',
            init_source,
        )
        sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        self.assertNotIn('key="logger_raw_profile"', sensor_source)

    def test_documentation_language_layout(self) -> None:
        self.assertTrue((ROOT / "README.md").is_file())
        self.assertFalse((ROOT / "README_EN.md").exists())
        self.assertFalse((ROOT / "README_FR.md").exists())
        self.assertFalse((ROOT / "README_DE.md").exists())
        localized = (
            "README_FR.md",
            "README_DE.md",
            "README_ES.md",
            "README_IT.md",
            "README_NL.md",
            "README_PL.md",
            "README_ZH.md",
        )
        for name in localized:
            self.assertTrue((ROOT / "docs" / name).is_file())
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("[Français](docs/README_FR.md)", root_readme)
        self.assertIn("[Deutsch](docs/README_DE.md)", root_readme)
        version = _load_json(INTEGRATION / "manifest.json")["version"]
        self.assertIn(f"**{version}**", root_readme)
        documentation_version = version.split("-beta.", 1)[0]
        for name in localized:
            self.assertIn(
                documentation_version,
                (ROOT / "docs" / name).read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
