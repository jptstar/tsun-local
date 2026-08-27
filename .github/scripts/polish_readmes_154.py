from pathlib import Path
import re

READMES = [
    Path("README.md"),
    Path("docs/README_FR.md"),
    Path("docs/README_DE.md"),
    Path("docs/README_ES.md"),
    Path("docs/README_IT.md"),
    Path("docs/README_NL.md"),
    Path("docs/README_PL.md"),
    Path("docs/README_ZH.md"),
]

for path in READMES:
    text = path.read_text(encoding="utf-8")

    # Product names should read like product names, not code identifiers.
    text = text.replace("**`Sunology PLAY2`**", "**Sunology PLAY2**")

    # Standalone horizontal rules should always breathe visually.
    text = re.sub(r"\n[ \t]*---[ \t]*\n", "\n\n---\n\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    # Keep the 1.5.4 summary and its documentation link as separate paragraphs.
    text = re.sub(r"(1\.5\.4[^\n]*\n)(📚)", r"\1\n\2", text, count=1)

    path.write_text(text.rstrip() + "\n", encoding="utf-8")

# Keep tests aligned with the cleaner public presentation rather than forcing
# a code-style product name.
path = Path("tests/test_play2_beta_communication.py")
text = path.read_text(encoding="utf-8")
text = text.replace("self.assertIn('`Sunology PLAY2`', readme)", "self.assertIn('Sunology PLAY2', readme)")
path.write_text(text, encoding="utf-8")

path = Path("tests/test_stable_151_localized_readmes.py")
text = path.read_text(encoding="utf-8")
text = text.replace('self.assertIn("`Sunology PLAY2`", text, filename)', 'self.assertIn("Sunology PLAY2", text, filename)')
path.write_text(text, encoding="utf-8")
