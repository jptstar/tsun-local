from pathlib import Path

root = Path(__file__).resolve().parents[2]
path = root / "tests/test_metadata.py"
text = path.read_text(encoding="utf-8")
old = '        self.assertIn("1.5.1: MP3000 field-validation update", index)\n'
new = '        self.assertIn("Sunology PLAY2 validated · 1.5.3 clear-text alarms", index)\n'
if old not in text:
    raise SystemExit("Expected stale public-site title assertion was not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
Path(__file__).unlink()
