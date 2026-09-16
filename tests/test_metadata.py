from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).parents[1]


class MetadataTests(unittest.TestCase):
    def test_manifest_version_has_release_metadata(self) -> None:
        manifest = json.loads(
            (ROOT / "custom_components" / "tsun_local" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+(?:[.-][0-9A-Za-z.]+)?$")
        self.assertEqual(manifest["integration_type"], "hub")
        self.assertEqual(manifest["iot_class"], "local_polling")

    def test_brand_assets_are_synchronized(self) -> None:
        repo_icon = ROOT / "icon.png"
        site_icon = ROOT / "docs" / "icon.png"
        hacs_icon = ROOT / "custom_components" / "tsun_local" / "icon.png"
        for path in (repo_icon, site_icon, hacs_icon):
            self.assertTrue(path.is_file(), path)
        self.assertEqual(repo_icon.read_bytes(), site_icon.read_bytes())
        self.assertEqual(repo_icon.read_bytes(), hacs_icon.read_bytes())

    def test_brand_assets_and_web_icon_are_synchronized(self) -> None:
        repo_icon = ROOT / "icon.png"
        site_icon = ROOT / "docs" / "icon.png"
        self.assertEqual(repo_icon.read_bytes(), site_icon.read_bytes())

    def test_translation_keys_match_strings(self) -> None:
        strings = json.loads(
            (ROOT / "custom_components" / "tsun_local" / "strings.json").read_text(
                encoding="utf-8"
            )
        )
        source_keys = set(strings["entity"]["sensor"])
        for path in sorted((ROOT / "custom_components" / "tsun_local" / "translations").glob("*.json")):
            translation = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(source_keys, set(translation["entity"]["sensor"]), path.name)

    def test_connectivity_binary_sensor_has_an_explicit_localized_name(self) -> None:
        strings = json.loads(
            (ROOT / "custom_components" / "tsun_local" / "strings.json").read_text(
                encoding="utf-8"
            )
        )
        binary = strings["entity"]["binary_sensor"]
        self.assertIn("connection_status", binary)
        self.assertTrue(binary["connection_status"]["name"])

    def test_device_identifiers_are_clear_and_mac_is_not_a_link(self) -> None:
        source = (ROOT / "custom_components" / "tsun_local" / "coordinator.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"Logger SN"', source)
        self.assertIn('"Inverter SN"', source)
        self.assertIn('"MAC"', source)
        self.assertNotIn('connections={("mac"', source)

    def test_raw_logger_profile_is_device_info_only(self) -> None:
        """Keep the raw profile out of entities and clean the beta.4 orphan."""
        sensor_source = (ROOT / "custom_components" / "tsun_local" / "sensor.py").read_text(
            encoding="utf-8"
        )
        strings = json.loads(
            (ROOT / "custom_components" / "tsun_local" / "strings.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertNotIn('key="logger_profile_raw"', sensor_source)
        self.assertNotIn("logger_profile_raw", strings["entity"]["sensor"])

    def test_documentation_language_layout(self) -> None:
        localized = [
            "README_FR.md",
            "README_DE.md",
            "README_ES.md",
            "README_IT.md",
            "README_NL.md",
            "README_PL.md",
            "README_ZH.md",
        ]
        for name in localized:
            self.assertTrue((ROOT / "docs" / name).is_file(), name)

        manifest = json.loads(
            (ROOT / "custom_components" / "tsun_local" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        documentation_series = ".".join(manifest["version"].split(".")[:2])
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
        ms2000 = (ROOT / "docs" / "tsol-ms2000-home-assistant.html").read_text(encoding="utf-8")
        sitemap = (ROOT / "docs" / "sitemap.xml").read_text(encoding="utf-8")
        robots = (ROOT / "docs" / "robots.txt").read_text(encoding="utf-8")

        self.assertIn('sunology-play2.html', index)
        self.assertIn('entities.html', index)
        self.assertIn('Windows diagnostic →', index)
        self.assertIn('Python diagnostic →', index)
        self.assertNotIn('Mac &amp; Linux diagnostic →', index)
        self.assertNotIn('test-your-inverter.html#mac-linux', index)
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

        self.assertIn("Sunology PLAY2", play2)
        self.assertIn("Home Assistant", play2)
        self.assertIn("TSUN Local", ms2000)
        self.assertIn("Home Assistant", ms2000)
        self.assertIn("sunology-play2.html", sitemap)
        self.assertIn("tsol-ms2000-home-assistant.html", sitemap)
        self.assertIn("Sitemap:", robots)


if __name__ == "__main__":
    unittest.main()
