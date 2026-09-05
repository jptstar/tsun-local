from pathlib import Path

root = Path(__file__).parents[1]
for rel in ("docs/HARDWARE_DUMP.md", "tools/README.md"):
    path = root / rel
    text = path.read_text(encoding="utf-8")
    text = text.replace("Windows GUI 1.2.0", "Windows GUI 1.3.0")
    text = text.replace("the current GUI is 1.2.0", "the current GUI is 1.3.0")
    path.write_text(text, encoding="utf-8")

path = root / "tools/README.md"
text = path.read_text(encoding="utf-8")
old = "No installation and no Python environment are required. The executable provides a small French/English interface, performs the same privacy-safe **strictly read-only** capture as `tsun_dump.py`, and writes the anonymized JSON report into the folder selected by the user."
new = "No installation and no Python environment are required. The executable provides a compact French/English **scroll-free main screen** with the three essential steps visible at once. Advanced settings and technical logs open separately, while the same privacy-safe **strictly read-only** `tsun_dump.py` engine writes the anonymized JSON report into the selected folder."
if old not in text:
    raise RuntimeError("tools/README.md wording anchor not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")

# Trigger the one-shot sync workflow after it exists on the branch.
