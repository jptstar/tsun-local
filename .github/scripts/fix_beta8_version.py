from pathlib import Path

path = Path("README.md")
text = path.read_text(encoding="utf-8")
text = text.replace("<strong>1.4.0-beta.8</strong>", "**1.4.0-beta.8**", 1)
path.write_text(text, encoding="utf-8")
