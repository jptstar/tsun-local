#!/usr/bin/env python3
"""Remove stale wording that implies public Mac builds are not available yet."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPLACEMENTS = {
    "Which Mac should I download once the signed builds are published?": "Which Mac should I download?",
    "Which Mac should I download once the signed builds are published?**": "Which Mac should I download?**",
    "Quel Mac choisir lorsque les builds signés seront publiés ?": "Quel Mac choisir ?",
    "Quel Mac choisir lorsque les builds signes seront publies ?": "Quel Mac choisir ?",
}

PATHS = [
    ROOT / "README.md",
    ROOT / "tools" / "README.md",
    ROOT / "docs" / "HARDWARE_DUMP.md",
    ROOT / "docs" / "DIRECT_DIAGNOSTIC_UPLOAD_TEST.md",
    *sorted((ROOT / "docs").glob("README_*.md")),
]

for path in PATHS:
    text = path.read_text(encoding="utf-8")
    updated = text
    for old, new in REPLACEMENTS.items():
        updated = updated.replace(old, new)
    if updated != text:
        path.write_text(updated, encoding="utf-8")

print("Current Mac download wording synchronized.")
