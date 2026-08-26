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

VERSION_PATTERN = re.compile(r"<strong>1\.5\.\d+(?:-beta\.\d+)?</strong>")


class Stable151LocalizedReadmeTests(unittest.TestCase):
    def test_all_localized_readmes_follow_current_structure(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            self.assertRegex(text, VERSION_PATTERN, filename)
            self.assertIn("### 1511", text, filename)
            self.assertIn("### 02B0", text, filename)
            self.assertIn("### 1097", text, filename)
            self.assertIn("MP3000_FIELD_VALIDATION.md", text, filename)
            self.assertIn("HARDWARE_DUMP.md", text, filename)

    def test_release_specific_firmware_details_are_not_required_in_readmes(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            start_1511 = text.index("### 1511")
            start_02b0 = text.index("### 02B0", start_1511)
            section_1511 = text[start_1511:start_02b0]
            self.assertIn("MP3000_FIELD_VALIDATION.md", section_1511, filename)

    def test_removed_1511_power_candidate_is_not_back_in_localized_tables(self) -> None:
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
            start_1511 = text.index("### 1511")
            start_02b0 = text.index("### 02B0", start_1511)
            section_1511 = text[start_1511:start_02b0].lower()
            for phrase in candidate_words:
                self.assertNotIn(phrase.lower(), section_1511, filename)


if __name__ == "__main__":
    unittest.main()
