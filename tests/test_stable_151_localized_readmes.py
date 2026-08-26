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


class Stable151LocalizedReadmeTests(unittest.TestCase):
    def test_all_localized_readmes_cover_current_protocol_families(self) -> None:
        version_pattern = re.compile(r"<strong>1\.5\.\d+</strong>")
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            self.assertRegex(text, version_pattern, filename)
            self.assertIn("1511", text, filename)
            self.assertIn("02B0", text, filename)
            self.assertIn("1097", text, filename)
            self.assertIn("TSOL-MP3000", text, filename)
            self.assertIn("TSOL-MX500", text, filename)

    def test_1511_sections_keep_field_validation_context_when_present(self) -> None:
        """Keep legacy structured READMEs useful without freezing their layout."""
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            if "### 1511" not in text:
                self.assertIn("TSOL-MP3000", text, filename)
                continue
            start_1511 = text.index("### 1511")
            start_02b0 = text.index("### 02B0", start_1511)
            section_1511 = text[start_1511:start_02b0]
            self.assertIn("MP3000_FIELD_VALIDATION.md", section_1511, filename)

    def test_removed_1511_power_candidate_is_not_back_in_localized_readmes(self) -> None:
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
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8").lower()
            for phrase in candidate_words:
                self.assertNotIn(phrase.lower(), text, filename)


if __name__ == "__main__":
    unittest.main()
