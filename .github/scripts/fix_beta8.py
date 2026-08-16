from pathlib import Path
import re

p1511 = Path("custom_components/tsun_local/protocols/protocol_1511.py")
text = p1511.read_text(encoding="utf-8")
text = text.replace(
    'data[f"{prefix}_energy_today"] = registers[base + 5] * 0.01',
    'data[f"{prefix}_energy_today"] = registers.get(base + 5, 0) * 0.01',
    1,
)
p1511.write_text(text, encoding="utf-8")

readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
language_block = "[English](README.md) · [Français](docs/README_FR.md) · [Deutsch](docs/README_DE.md) · [Nederlands](docs/README_NL.md) · [Italiano](docs/README_IT.md) · [Español](docs/README_ES.md) · [Polski](docs/README_PL.md) · [简体中文](docs/README_ZH.md)"
text = re.sub(
    r'<p align="center">\n  <a href="README\.md">English</a>.*?</p>',
    f'<p align="center">\n\n{language_block}\n\n</p>',
    text,
    count=1,
    flags=re.S,
)
text = text.replace(
    '<p align="center"><strong>Direct local access for compatible TSUN micro-inverters in Home Assistant.</strong></p>',
    '<p align="center"><strong>Direct local access for compatible TSUN micro-inverters in Home Assistant.</strong><br><strong>1.4.0-beta.8</strong></p>',
    1,
)
readme.write_text(text, encoding="utf-8")

for path in Path("docs").glob("README_*.md"):
    text = path.read_text(encoding="utf-8")
    if text.startswith("# TSUN Local\n"):
        text = text.replace("# TSUN Local\n", "# TSUN Local 1.4.0\n", 1)
    path.write_text(text, encoding="utf-8")
