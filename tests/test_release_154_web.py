from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).parents[1]
DOCS = ROOT / "docs"


class Release160WebTests(unittest.TestCase):
    def test_all_public_pages_expose_star_cta_in_hero(self) -> None:
        for filename in (
            "index.html",
            "sunology-play2.html",
            "tsol-mp3000-home-assistant.html",
            "tsol-ms300-home-assistant.html",
            "tsol-mx500-home-assistant.html",
            "tsol-ms800-home-assistant.html",
            "tsol-ms2000-home-assistant.html",
            "test-your-inverter.html",
        ):
            text = (DOCS / filename).read_text(encoding="utf-8")
            header_end = text.index("</header>")
            hero = text[:header_end]
            self.assertIn("⭐ Star on GitHub", hero, filename)
            self.assertIn("https://github.com/jptstar/tsun-local", hero, filename)

    def test_all_public_pages_use_identical_footer(self) -> None:
        expected = (
            'TSUN Local · by <a href="https://github.com/jptstar">jptstar</a> · '
            '<a href="https://github.com/jptstar/tsun-local">GitHub</a> · '
            'Home Assistant · Read-only by design'
        )
        for path in DOCS.glob("*.html"):
            text = path.read_text(encoding="utf-8")
            if "<footer" in text:
                self.assertIn(expected, text, path.name)

    def test_hardware_test_page_promotes_current_diagnostic(self) -> None:
        text = (DOCS / "test-your-inverter.html").read_text(encoding="utf-8")
        self.assertIn("Windows diagnostic", text)
        self.assertIn("Full Python diagnostic — Linux and advanced users", text)
        self.assertIn("TSUN-Local-Diagnostic-Python.zip", text)
        self.assertNotIn('id="mac-linux"', text)
        self.assertNotIn("TSUN-Local-Diagnostic-macOS-", text)
        self.assertNotIn("TSUN-Local-Diagnostic-Linux-", text)
        self.assertIn("Strictly read-only", text)
        self.assertIn("Direct upload", text)
        self.assertIn("TSL receipt", text)

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
            text = (DOCS / filename).read_text(encoding="utf-8")
            self.assertIn("https://my.home-assistant.io/badges/hacs_repository.svg", text, filename)
            self.assertNotRegex(text, r">(?:Add TSUN Local to HACS|Add to HACS)</a>", filename)

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
        self.assertIn("product_compliance_type_raw", (DOCS / "entities.html").read_text(encoding="utf-8"))

    def test_public_pages_do_not_advertise_beta_160(self) -> None:
        for path in DOCS.glob("*.html"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("1.6.0-beta", text, path.name)

    def test_public_pages_have_unique_h1_and_seo(self) -> None:
        titles: set[str] = set()
        descriptions: set[str] = set()
        for path in DOCS.glob("*.html"):
            text = path.read_text(encoding="utf-8")
            title_match = re.search(r"<title>(.*?)</title>", text, re.DOTALL)
            description_match = re.search(
                r'<meta name="description" content="([^"]+)">', text
            )
            h1_count = len(re.findall(r"<h1(?:\s[^>]*)?>", text))
            if title_match and description_match:
                title = title_match.group(1).strip()
                description = description_match.group(1).strip()
                self.assertNotIn(title, titles, path.name)
                self.assertNotIn(description, descriptions, path.name)
                titles.add(title)
                descriptions.add(description)
            self.assertLessEqual(h1_count, 1, path.name)

    def test_public_site_stays_on_stable_release_during_beta(self) -> None:
        text = (DOCS / "index.html").read_text(encoding="utf-8")
        self.assertIn("TSUN Local 1.6.2 highlights", text)
        self.assertIn("NEW IN 1.6.2", text)
        self.assertNotIn("beta", text.lower())

    def test_sitemap_contains_validated_hardware_pages(self) -> None:
        sitemap = (DOCS / "sitemap.xml").read_text(encoding="utf-8")
        for filename in (
            "entities.html",
            "sunology-play2.html",
            "tsol-mp3000-home-assistant.html",
            "tsol-ms300-home-assistant.html",
            "tsol-mx500-home-assistant.html",
            "tsol-ms800-home-assistant.html",
            "tsol-ms2000-home-assistant.html",
            "test-your-inverter.html",
            "contributors.html",
        ):
            self.assertIn(filename, sitemap)


if __name__ == "__main__":
    unittest.main()
