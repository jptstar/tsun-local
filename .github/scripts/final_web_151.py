from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
entities_path = ROOT / "docs" / "entities.html"
text = entities_path.read_text(encoding="utf-8")
text = text.replace(
    "<tr><td><strong>Total</strong></td><td><strong>108</strong></td><td>56 enabled · 49 advanced</td></tr>",
    "<tr><td><strong>Total</strong></td><td><strong>108</strong></td><td>59 enabled · 49 advanced</td></tr>",
)
text = text.replace(
    "the beta field-validation work adds no duplicate alarm entities.",
    "the 1.5.1 field-validation work adds no duplicate alarm entities.",
)
entities_path.write_text(text, encoding="utf-8")

metadata_path = ROOT / "tests" / "test_metadata.py"
metadata = metadata_path.read_text(encoding="utf-8")
needle = '        self.assertIn("Device and logger</td><td>8</td>", entities)\n'
extra = '        self.assertIn("59 enabled · 49 advanced", entities)\n        self.assertNotIn("beta field-validation work", entities)\n'
if extra not in metadata:
    if needle not in metadata:
        raise SystemExit("metadata insertion point missing")
    metadata = metadata.replace(needle, needle + extra, 1)
metadata_path.write_text(metadata, encoding="utf-8")

final = entities_path.read_text(encoding="utf-8")
for forbidden in ("56 enabled · 49 advanced", "beta field-validation work", "105 entities with 6 PV inputs"):
    if forbidden in final:
        raise SystemExit(f"stale entity page text remains: {forbidden}")
print("Final 1.5.1 web consistency fixed")
