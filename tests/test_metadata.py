# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Project metadata, privacy, and translation consistency tests."""

from __future__ import annotations

import json
from pathlib import Path
import re
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
                translated["entity"]["binary_sensor"]["communication_online"]["name"],
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
        self.assertNotIn("logger_raw_profile", strings["entity"]["sensor"])
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
        self.assertIn(
            'href="https://github.com/jptstar/tsun-local/blob/main/docs/README_FR.md">Français</a>',
            root_readme,
        )
        self.assertIn(
            'href="https://github.com/jptstar/tsun-local/blob/main/docs/README_DE.md">Deutsch</a>',
            root_readme,
        )
        version = _load_json(INTEGRATION / "manifest.json")["version"]
        self.assertIn(f"<strong>{version}</strong>", root_readme)
        documentation_version = version.split("-beta.", 1)[0]
        if "-beta." in version:
            self.assertIn(
                documentation_version,
                (ROOT / "docs" / "README_FR.md").read_text(encoding="utf-8"),
            )
        else:
            documentation_series = ".".join(documentation_version.split(".")[:2])
            version_pattern = re.compile(rf"\b{re.escape(documentation_series)}\.\d+\b")
            for name in localized:
                self.assertRegex(
                    (ROOT / "docs" / name).read_text(encoding="utf-8"),
                    version_pattern,
                )

    def test_public_site_links_visual_entity_reference(self) -> None:
        index = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        entities = (ROOT / "docs" / "entities.html").read_text(encoding="utf-8")
        play2 = (ROOT / "docs" / "sunology-play2.html").read_text(encoding="utf-8")
        sitemap = (ROOT / "docs" / "sitemap.xml").read_text(encoding="utf-8")
        robots = (ROOT / "docs" / "robots.txt").read_text(encoding="utf-8")

        self.assertIn('entities.html', index)
        self.assertIn('sunology-play2.html', index)
        self.assertIn("Your inverter. Your network. Your data.", index)
        self.assertIn("Sunology PLAY2", index)
        self.assertIn("Automatic discovery", index)
        self.assertIn("Alarms you can actually read", index)
        self.assertIn('"@type": "WebSite"', index)
        self.assertIn('"Sunology PLAY2"', index)

        self.assertIn("TSUN Local Entities", entities)
        self.assertIn("Sunology PLAY2", entities)
        self.assertIn("Readable alarm entities", entities)
        self.assertIn("active_alarm_names", entities)
        self.assertIn("224 positions", entities)
        self.assertIn("64 positions", entities)
        self.assertIn("TSOL-MP3000", entities)
        self.assertIn('"@type":"BreadcrumbList"', entities)
        self.assertIn('name="twitter:card"', entities)

        self.assertIn("Sunology PLAY2 in Home Assistant", play2)
        self.assertIn("VALIDATED ON REAL SUNOLOGY PLAY2 HARDWARE", play2)
        self.assertIn("LSW5BLE_17_02B0_1.08-D1", play2)
        self.assertIn("No proxy", play2)

        expected_sitemap_urls = (
            "https://jptstar.github.io/tsun-local/",
            "https://jptstar.github.io/tsun-local/entities.html",
            "https://jptstar.github.io/tsun-local/sunology-play2.html",
            "https://jptstar.github.io/tsun-local/tsol-mp3000-home-assistant.html",
            "https://jptstar.github.io/tsun-local/test-your-inverter.html",
            "https://jptstar.github.io/tsun-local/contributors.html",
        )
        for url in expected_sitemap_urls:
            self.assertIn(f"<loc>{url}</loc>", sitemap)
        self.assertEqual(sitemap.count("<url>"), len(expected_sitemap_urls))
        self.assertNotIn("<lastmod>", sitemap)
        self.assertFalse((ROOT / "docs" / "sitemap.txt").exists())
        self.assertIn("Sitemap: https://jptstar.github.io/tsun-local/sitemap.xml", robots)
        self.assertNotIn("sitemap.txt", robots)

    def test_brand_assets_and_web_icon_are_synchronized(self) -> None:
        brand = INTEGRATION / "brand"
        expected = ("icon.png", "icon@2x.png", "logo.png", "logo@2x.png")
        for name in expected:
            data = (brand / name).read_bytes()
            self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"), name)
            self.assertGreater(len(data), 1024, name)
        self.assertEqual((brand / "icon.png").read_bytes(), (brand / "logo.png").read_bytes())
        self.assertEqual((brand / "icon@2x.png").read_bytes(), (brand / "logo@2x.png").read_bytes())
        self.assertEqual((ROOT / "docs" / "icon.png").read_bytes(), (brand / "icon.png").read_bytes())


if __name__ == "__main__":
    unittest.main()
