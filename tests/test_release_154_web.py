from __future__ import annotations

from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"
PAGES_DIR = DOCS / "pages"
# Keep one shared, minimal footer contract across every public HTML page.
FOOTER = 'TSUN Local · by <a href="https://github.com/jptstar">jptstar</a> · <a href="https://github.com/jptstar/tsun-local">GitHub</a> · Home Assistant · Read-only by design'
PAGES = ("index.html", "entities.html", "sunology-play2.html", "tsol-mp3000-home-assistant.html", "tsol-ms300-home-assistant.html", "tsol-mx500-home-assistant.html", "tsol-ms800-home-assistant.html", "tsol-ms2000-home-assistant.html", "contributors.html", "test-your-inverter.html")


def _page_path(filename: str) -> Path:
    """Return the source path for a public page while keeping its public URL stable."""
    return DOCS / "index.html" if filename == "index.html" else PAGES_DIR / filename


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
            self.assertIn("NEW IN 1.6.2", index)
        else:
            self.assertIn(manifest["version"], index)

    def test_public_pages_have_unique_h1_and_seo(self) -> None:
        seen = set()
        for filename in PAGES:
            text = _page_path(filename).read_text(encoding="utf-8")
            h1 = re.search(r"<h1>(.*?)</h1>", text, flags=re.S)
            self.assertIsNotNone(h1, filename)
            self.assertNotIn(h1.group(1), seen, filename)
            seen.add(h1.group(1))
            self.assertIn('name="description"', text, filename)
            self.assertIn('rel="canonical"', text, filename)

    def test_all_public_pages_use_identical_footer(self) -> None:
        for filename in PAGES:
            text = _page_path(filename).read_text(encoding="utf-8")
            match = re.search(r'<footer class="wrap">(.*?)</footer>', text, flags=re.S)
            self.assertIsNotNone(match, filename)
            self.assertEqual(FOOTER, match.group(1), filename)
            self.assertNotIn("⭐ Star on GitHub", match.group(1), filename)

    def test_all_public_pages_expose_star_cta_in_hero(self) -> None:
        for filename in PAGES:
            text = _page_path(filename).read_text(encoding="utf-8")
            hero = text.split("</header>", 1)[0]
            self.assertIn('aria-label="Star TSUN Local on GitHub"', hero, filename)
            self.assertIn("⭐ Star on GitHub", hero, filename)

    def test_public_pages_do_not_advertise_beta_160(self) -> None:
        for filename in PAGES:
            text = _page_path(filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("1.6.0 beta", text, filename)
            self.assertNotIn("1.6.0-beta", text, filename)

    def test_sitemap_contains_validated_hardware_pages(self) -> None:
        sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
        for filename in (
            "tsol-mp3000-home-assistant.html",
            "tsol-ms300-home-assistant.html",
            "tsol-mx500-home-assistant.html",
            "tsol-ms800-home-assistant.html",
            "tsol-ms2000-home-assistant.html",
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
        self.assertIn("tsol-ms300-home-assistant.html", text)
        self.assertIn("tsol-mx500-home-assistant.html", text)
        self.assertIn("tsol-ms800-home-assistant.html", text)
        self.assertIn("tsol-ms2000-home-assistant.html", text)
        self.assertIn("paloindici", text)
        self.assertIn("NEW IN 1.6.2", text)
        self.assertIn("test-your-inverter.html#windows", text)
        self.assertIn("test-your-inverter.html#python", text)
        self.assertNotIn("test-your-inverter.html#mac-linux", text)
        self.assertIn("entities.html", text)
        self.assertIn("product_compliance_type_raw", _page_path("entities.html").read_text(encoding="utf-8"))

    def test_public_hacs_actions_use_official_badge(self) -> None:
        for filename in (
            "index.html",
            "sunology-play2.html",
            "tsol-mp3000-home-assistant.html",
            "tsol-ms300-home-assistant.html",
            "tsol-mx500-home-assistant.html",
            "tsol-ms800-home-assistant.html",
            "tsol-ms2000-home-assistant.html",
        ):
            text = _page_path(filename).read_text(encoding="utf-8")
            self.assertIn("https://my.home-assistant.io/badges/hacs_repository.svg", text, filename)
            self.assertNotRegex(text, r">(?:Add TSUN Local to HACS|Add to HACS)</a>", filename)

    def test_hardware_test_page_promotes_current_diagnostic(self) -> None:
        text = _page_path("test-your-inverter.html").read_text(encoding="utf-8")
        self.assertIn("TSUN Local 1.6.0", text)
        self.assertNotIn("TSUN Local 1.5.3", text)
        self.assertIn("TSUN-Local-Diagnostic.exe", text)
        self.assertIn("disable the affected TSUN Local config entry", text)


if __name__ == "__main__":
    unittest.main()
