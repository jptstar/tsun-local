from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"
FOOTER = 'TSUN Local · by <a href="https://github.com/jptstar">jptstar</a> · <a href="https://github.com/jptstar/tsun-local">GitHub</a> · Home Assistant · Read-only by design'
PAGES = ("index.html", "entities.html", "sunology-play2.html", "contributors.html", "test-your-inverter.html")


class Release154WebTests(unittest.TestCase):
    def test_manifest_is_stable_154(self) -> None:
        manifest = json.loads((ROOT / "custom_components" / "tsun_local" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual("1.5.4", manifest["version"])

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

    def test_public_pages_do_not_advertise_beta_154(self) -> None:
        for filename in PAGES:
            text = (DOCS / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("1.5.4 beta", text, filename)
            self.assertNotIn("1.5.4-beta", text, filename)

    def test_homepage_keeps_project_identity(self) -> None:
        text = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn("Your inverter. Your network. Your data.", text)
        self.assertIn("TSUN microinverters in Home Assistant", text)
        self.assertIn("Sunology PLAY2", text)
        self.assertIn("test-your-inverter.html", text)
        self.assertIn("contributors.html", text)
        self.assertIn("NEW IN 1.5.4", text)
        self.assertIn("product_compliance_type_raw", (DOCS / "entities.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
