from pathlib import Path

FILES = {
    "README.md": ("docs/MP3000_FIELD_VALIDATION.md", "MP3000 / TITAN validation", "corresponding `-D` variants"),
    "docs/README_FR.md": ("MP3000_FIELD_VALIDATION.md", "Validation MP3000 / TITAN", "variantes `-D` correspondantes"),
    "docs/README_DE.md": ("MP3000_FIELD_VALIDATION.md", "MP3000 / TITAN Validierung", "entsprechende `-D`-Varianten"),
    "docs/README_ES.md": ("MP3000_FIELD_VALIDATION.md", "Validación MP3000 / TITAN", "variantes `-D` correspondientes"),
    "docs/README_IT.md": ("MP3000_FIELD_VALIDATION.md", "Validazione MP3000 / TITAN", "varianti `-D` corrispondenti"),
    "docs/README_NL.md": ("MP3000_FIELD_VALIDATION.md", "MP3000 / TITAN-validatie", "overeenkomstige `-D`-varianten"),
    "docs/README_PL.md": ("MP3000_FIELD_VALIDATION.md", "Walidacja MP3000 / TITAN", "odpowiednie warianty `-D`"),
    "docs/README_ZH.md": ("MP3000_FIELD_VALIDATION.md", "MP3000 / TITAN 验证", "对应的 `-D` 变体"),
}

for filename, (mp_link, mp_label, d_variant) in FILES.items():
    path = Path(filename)
    text = path.read_text(encoding="utf-8")
    text = text.replace("**Sunology PLAY2**", "**`Sunology PLAY2`**")
    text = text.replace("corresponding `-D` variants", d_variant)
    marker = "</details>\n\n"
    addition = f"📚 **[{mp_label}]({mp_link})**\n\n"
    if addition not in text:
        if marker not in text:
            raise SystemExit(f"{filename}: compatibility details marker missing")
        text = text.replace(marker, marker + addition, 1)
    text = "\n".join(line.rstrip() for line in text.splitlines()).rstrip() + "\n"
    path.write_text(text, encoding="utf-8")

Path("tests/test_stable_151_localized_readmes.py").write_text('''from __future__ import annotations

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

VERSION_PATTERN = re.compile(r"<strong>1\\.5\\.4</strong>")


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
            compact = text.split("\\n---\\n", 2)[1].lower()
            for phrase in candidate_words:
                self.assertNotIn(phrase.lower(), compact, filename)


if __name__ == "__main__":
    unittest.main()
''', encoding="utf-8")

play2_test = Path("tests/test_play2_beta_communication.py")
text = play2_test.read_text(encoding="utf-8")
text = text.replace("self.assertIn('Sunology PLAY2 is now validated', readme)", "self.assertIn('Sunology PLAY2 is validated on real Home Assistant hardware', readme)")
play2_test.write_text(text, encoding="utf-8")
