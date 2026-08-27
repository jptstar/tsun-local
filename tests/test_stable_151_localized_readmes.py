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

VERSION_PATTERN = re.compile(r"<strong>1\.5\.4</strong>")


class Stable154LocalizedReadmeTests(unittest.TestCase):
    def test_all_localized_readmes_follow_compact_current_structure(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            self.assertRegex(text, VERSION_PATTERN, filename)
            self.assertEqual(text.count("| **1511** | TITAN |"), 1, filename)
            self.assertEqual(text.count("| **02B0** | GEN3 / GEN3 PLUS |"), 1, filename)
            self.assertEqual(text.count("| **1097** | GEN3 / GEN3 PLUS |"), 1, filename)
            self.assertIn("`Sunology PLAY2`", text, filename)
            self.assertIn("MP3000_FIELD_VALIDATION.md", text, filename)
            self.assertIn("HARDWARE_DUMP.md", text, filename)
            self.assertIn("PLAY2_LOCAL_RESEARCH.md", text, filename)
            self.assertIn("ha-solarman", text, filename)
            self.assertIn("dca31", text, filename)

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
