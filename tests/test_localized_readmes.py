from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).parents[1]

FILES = (
    "README_FR.md",
    "README_DE.md",
    "README_ES.md",
    "README_IT.md",
    "README_NL.md",
    "README_PL.md",
    "README_ZH.md",
)

ROOT_README = (ROOT / "README.md").read_text(encoding="utf-8")
ROOT_VERSION_MATCH = re.search(r"<strong>(\d+\.\d+\.\d+)</strong>", ROOT_README)
if ROOT_VERSION_MATCH is None:
    raise RuntimeError("Public stable version not found in README.md")
PUBLIC_STABLE_VERSION = ROOT_VERSION_MATCH.group(1)
VERSION_PATTERN = re.compile(
    rf"<strong>{re.escape(PUBLIC_STABLE_VERSION)}</strong>"
)


class LocalizedReadmeTests(unittest.TestCase):
    def test_all_localized_readmes_follow_compact_current_structure(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            self.assertRegex(text, VERSION_PATTERN, filename)
            self.assertEqual(text.count("| **1511** | TITAN |"), 1, filename)
            self.assertEqual(text.count("| **02B0** | GEN3 / GEN3 PLUS |"), 1, filename)
            self.assertEqual(text.count("| **1097** | GEN4 |"), 1, filename)
            self.assertIn("Sunology PLAY2", text, filename)
            self.assertIn("**Sunology PLAY2**<br>**TSOL-MS300**<br>**TSOL-MS800**<br>**TSOL-MS2000**<br>**TSOL-MX450**<br>**TSOL-MX500**", text, filename)
            self.assertIn("**Sunology PLAY2 (GEN4)**<br>**TSOL-MX3000D**", text, filename)
            self.assertIn("tsol-mx500-home-assistant.html", text, filename)
            self.assertIn("tsol-ms300-home-assistant.html", text, filename)
            self.assertIn("tsol-mx450-home-assistant.html", text, filename)
            self.assertIn("tsol-mx3000d-home-assistant.html", text, filename)
            self.assertIn("sunology-go-home-assistant.html", text, filename)
            self.assertIn("tsol-ms800-balcony-home-assistant.html", text, filename)
            self.assertIn("Valentin Fleuret", text, filename)
            self.assertNotIn("**TSOL-MX3000D** (observed)", text, filename)
            self.assertIn("phklrz", text, filename)
            self.assertNotIn("**TSOL-MX450** (observed)", text, filename)
            self.assertIn("LSW5_SSL_02B0_1.05", text, filename)
            self.assertIn("tsol-ms800-home-assistant.html", text, filename)
            self.assertIn("tsol-ms2000-home-assistant.html", text, filename)
            likely_02b0 = next(line for line in text.splitlines() if line.startswith("- **02B0"))
            self.assertNotIn("`TSOL-MX450`", likely_02b0, filename)
            self.assertNotIn("`TSOL-MS800`", likely_02b0, filename)
            self.assertNotIn("`TSOL-MS2000`", likely_02b0, filename)
            likely_1097 = next(line for line in text.splitlines() if line.startswith("- **1097"))
            self.assertNotIn("`TSOL-MX3000D`", likely_1097, filename)
            self.assertIn("MP3000_FIELD_VALIDATION.md", text, filename)
            self.assertIn("HARDWARE_DUMP.md", text, filename)
            self.assertIn("PLAY2_LOCAL_RESEARCH.md", text, filename)
            self.assertIn("ha-solarman", text, filename)
            self.assertIn("dca31", text, filename)
            self.assertIn("paloindici", text, filename)


    def test_github_and_hacs_readme_compatibility_lists_are_vertical_and_sorted(self) -> None:
        # HACS displays the repository README, so validate it alongside every translation.
        expected = {
            "1511": ["**TSOL-MP3000**"],
            "02B0": [
                "**Sunology PLAY2**",
                "**TSOL-MS300**",
                "**TSOL-MS800**",
                "**TSOL-MS2000**",
                "**TSOL-MX450**",
                "**TSOL-MX500**",
                "**Sunology GO** 🧪",
                "**TSOL-MS800 Balcony** 🧪",
            ],
            "1097": ["**Sunology PLAY2 (GEN4)**", "**TSOL-MX3000D**"],
        }
        for path in (ROOT / "README.md", *(ROOT / "docs" / filename for filename in FILES)):
            content = path.read_text(encoding="utf-8")
            for protocol, models in expected.items():
                matching = [line for line in content.splitlines() if line.startswith(f"| **{protocol}** |")]
                self.assertEqual(len(matching), 1, (path.name, protocol))
                columns = [part.strip() for part in matching[0].split("|")]
                self.assertEqual(len(columns), 6, (path.name, protocol))
                self.assertEqual(columns[3].split("<br>"), models, (path.name, protocol))
                self.assertTrue(columns[4].startswith("✅"), (path.name, protocol))

    def test_verbose_play2_transport_details_live_outside_readmes(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            self.assertNotIn("LSW5BLE_17_02B0_1.08-D1", text, filename)
            self.assertNotIn("sensor_list=0x02B0", text, filename)
            self.assertNotIn("0x4510", text, filename)

    def test_removed_1511_power_candidate_is_not_back_in_compact_compatibility(self) -> None:
        candidate_words = (
            "niveau de puissance candidat",
            "leistungsniveau (kandidat)",
            "nivel de potencia (candidato)",
            "livello di potenza (candidato)",
            "vermogensniveau (kandidaat)",
            "poziom mocy (kandydat)",
            "功率水平（候选）",
        )
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            compact = text.split("\n---\n", 2)[1].lower()
            for phrase in candidate_words:
                self.assertNotIn(phrase.lower(), compact, filename)


if __name__ == "__main__":
    unittest.main()
