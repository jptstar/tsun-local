from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "tsun_local"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


class MetadataTests(unittest.TestCase):
    def test_brand_assets_and_web_icon_are_synchronized(self) -> None:
        brand = INTEGRATION / "brand"
        self.assertTrue((brand / "icon.png").is_file())
        self.assertTrue((brand / "icon@2x.png").is_file())
        self.assertTrue((brand / "logo.png").is_file())
        self.assertTrue((brand / "logo@2x.png").is_file())
        self.assertEqual((brand / "icon.png").read_bytes(), (ROOT / "docs" / "icon.png").read_bytes())

    def test_connectivity_binary_sensor_has_an_explicit_localized_name(self) -> None:
        strings = _load_json(INTEGRATION / "strings.json")
        translations = INTEGRATION / "translations"
        key = "connectivity"
        self.assertIn(key, strings["entity"]["binary_sensor"])
        for path in translations.glob("*.json"):
            language = _load_json(path)
            self.assertIn(key, language["entity"]["binary_sensor"], path.name)
            self.assertTrue(language["entity"]["binary_sensor"][key]["name"], path.name)

    def test_device_identifiers_are_clear_and_mac_is_not_a_link(self) -> None:
        """Keep both SN values explicit and the MAC diagnostic non-clickable."""
        strings = _load_json(INTEGRATION / "strings.json")
        for key in ("inverter_serial_number", "logger_serial_number", "logger_mac_address"):
            self.assertIn(key, strings["entity"]["sensor"])
        sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        self.assertNotIn("device_class=SensorDeviceClass.URL", sensor_source)

    def test_raw_logger_profile_is_device_info_only(self) -> None:
        """Keep the raw profile out of entities and clean the beta.4 orphan."""
        sensor_source = (INTEGRATION / "sensor.py").read_text(encoding="utf-8")
        binary_source = (INTEGRATION / "binary_sensor.py").read_text(encoding="utf-8")
        self.assertNotIn("raw_logger_profile", sensor_source)
        self.assertNotIn("raw_logger_profile", binary_source)

    def test_translation_keys_match_strings(self) -> None:
        strings = _load_json(INTEGRATION / "strings.json")
        source = strings["entity"]
        for path in (INTEGRATION / "translations").glob("*.json"):
            translated = _load_json(path)["entity"]
            self.assertEqual(set(source), set(translated), path.name)
            for platform, entities in source.items():
                self.assertEqual(set(entities), set(translated[platform]), f"{path.name}:{platform}")

    def test_manifest_version_has_matching_changelog_entry(self) -> None:
        version = _load_json(INTEGRATION / "manifest.json")["version"]
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## [{version}]", changelog)

    def test_public_site_links_visual_entity_reference(self) -> None:
        index = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn("entities.html", index)

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
        self.assertIn('href="https://github.com/jptstar/tsun-local/blob/main/docs/README_FR.md">Français</a>', root_readme)
        self.assertIn('href="https://github.com/jptstar/tsun-local/blob/main/docs/README_DE.md">Deutsch</a>', root_readme)
        version = _load_json(INTEGRATION / "manifest.json")["version"]
        self.assertIn(f"**{version}**", root_readme)
        documentation_version = version.split("-beta.", 1)[0]
        if "-beta." in version:
            self.assertIn(
                documentation_version,
                (ROOT / "docs" / "README_FR.md").read_text(encoding="utf-8"),
            )
        else:
            for name in localized:
                self.assertIn(
                    documentation_version,
                    (ROOT / "docs" / name).read_text(encoding="utf-8"),
                    name,
                )


if __name__ == "__main__":
    unittest.main()
