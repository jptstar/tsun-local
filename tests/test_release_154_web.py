from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"
FOOTER = 'TSUN Local · by <a href="https://github.com/jptstar">jptstar</a> · <a href="https://github.com/jptstar/tsun-local">GitHub</a> · Home Assistant · Read-only by design'
PAGES = ("index.html", "entities.html", "sunology-play2.html", "tsol-mp3000-home-assistant.html", "tsol-mx500-home-assistant.html", "tsol-ms800-home-assistant.html", "contributors.html", "test-your-inverter.html")


class Release160WebTests(unittest.TestCase):
    def test_public_site_stays_on_stable_release_during_beta(self) -> None:
        manifest = json.loads((ROOT / "custom_components" / "tsun_local" / "manifest.json").read_text(encoding="utf-8"))
        self.assertRegex(
            manifest["version"],
            r"^\d+\.\d+\.\d+(?:-beta\.\d+)?$",
        )
        index = (DOCS / "index.html").read_text(encoding="utf-8")
        if "-beta." in manifest["version"]:
            self.assertNotIn(manifest["version"], index)
            self.assertIn("NEW IN 1.6.0", index)
        else:
            self.assertIn(manifest["version"], index)

    def test_public_pages_have_unique_h1_and_seo(self) -> None:
        seen = set()
        for filename in PAGES:
            text = (DOCS / filename).read_text(encoding="utf-8")
            h1 = re.search(r"<h1>(.*?)</h1>", text, flags=re.S)
            self.assertIsNotNone(h1, filename)
            self.assertNotIn(h1.group(1), seen, filename)
            seen.add(h1.group(1))
            self.assertIn('name="description"', text, filename)
            self.assertIn('rel="canonical"', text, filename)

    def test_all_public_pages_use_identical_footer(self) -> None:
        for filename in PAGES:
            text = (DOCS / filename).read_text(encoding="utf-8")
            match = re.search(r'<footer class="wrap">(.*?)</footer>', text, flags=re.S)
            self.assertIsNotNone(match, filename)
            self.assertEqual(FOOTER, match.group(1), filename)

    def test_public_pages_do_not_advertise_beta_160(self) -> None:
        for filename in PAGES:
            text = (DOCS / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("1.6.0 beta", text, filename)
            self.assertNotIn("1.6.0-beta", text, filename)

    def test_sitemap_contains_validated_hardware_pages(self) -> None:
        sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
        for filename in (
            "tsol-mp3000-home-assistant.html",
            "tsol-mx500-home-assistant.html",
            "tsol-ms800-home-assistant.html",
            "sunology-play2.html",
        ):
            self.assertIn(filename, sitemap)

    def test_homepage_keeps_project_identity(self) -> None:
        text = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn("Your inverter. Your network. Your data.", text)
        self.assertIn("TSUN microinverters in Home Assistant", text)
        self.assertIn("Sunology PLAY2", text)
        self.assertIn("test-your-inverter.html", text)
        self.assertIn("contributors.html", text)
        self.assertIn("tsol-mx500-home-assistant.html", text)
        self.assertIn("tsol-ms800-home-assistant.html", text)
        self.assertIn("NEW IN 1.6.0", text)
        self.assertIn("product_compliance_type_raw", (DOCS / "entities.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
