from __future__ import annotations

from pathlib import Path
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
    def test_all_localized_readmes_describe_stable_151(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            self.assertIn("<strong>1.5.1</strong>", text, filename)
            self.assertIn("DSP", text, filename)
            self.assertIn("QCPU1", text, filename)
            self.assertIn("QCPU2", text, filename)

    def test_dsp_qcpu_firmware_is_1511_only(self) -> None:
        for filename in FILES:
            text = (ROOT / "docs" / filename).read_text(encoding="utf-8")
            start_1511 = text.index("### 1511")
            start_02b0 = text.index("### 02B0", start_1511)
            start_1097 = text.index("### 1097", start_02b0)
            section_1511 = text[start_1511:start_02b0]
            section_02b0 = text[start_02b0:start_1097]
            self.assertIn("DSP", section_1511, filename)
            self.assertIn("QCPU", section_1511, filename)
            self.assertNotIn("DSP", section_02b0, filename)
            self.assertNotIn("QCPU", section_02b0, filename)

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
