#!/usr/bin/env python3
"""Verify the public diagnostic documentation stays on canonical assets."""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

WINDOWS_ASSET = "TSUN-Local-Diagnostic.exe"
PYTHON_ASSET = "TSUN-Local-Diagnostic-Python.zip"
DUMPER_ASSET = "tsun_dump.py"

PUBLIC_FILES = (
    ROOT / "README.md",
    ROOT / "tools" / "README.md",
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "test-your-inverter.html",
    ROOT / "docs" / "HARDWARE_DUMP.md",
    ROOT / "docs" / "DIRECT_DIAGNOSTIC_UPLOAD_TEST.md",
    *sorted((ROOT / "docs").glob("README_*.md")),
)

ALLOWED_RELEASE_ASSETS = {
    WINDOWS_ASSET,
    WINDOWS_ASSET + ".sha256",
    PYTHON_ASSET,
    PYTHON_ASSET + ".sha256",
    DUMPER_ASSET,
    DUMPER_ASSET + ".sha256",
}

DIAGNOSTIC_ASSET_RE = re.compile(
    r"TSUN-Local-Diagnostic(?:\.exe(?:\.sha256)?|-[A-Za-z0-9_.-]+)"
)


def verify() -> None:
    """Fail when public documentation drifts from the supported distribution."""
    texts = {path: path.read_text(encoding="utf-8") for path in PUBLIC_FILES}
    failures: list[str] = []

    required = {
        ROOT / "README.md": (
            WINDOWS_ASSET,
            PYTHON_ASSET,
            "Sunology PLAY2 (GEN4)",
            "1097",
        ),
        ROOT / "docs" / "index.html": (
            "Windows diagnostic →",
            "Python diagnostic →",
            "Sunology PLAY2 GEN4",
            '<span class="compat-family">GEN4</span>',
            "1097",
        ),
        ROOT / "docs" / "test-your-inverter.html": (
            WINDOWS_ASSET,
            PYTHON_ASSET,
            'id="windows"',
            'id="python"',
        ),
    }

    for path, markers in required.items():
        text = texts[path]
        for marker in markers:
            if marker not in text:
                failures.append(f"{path.relative_to(ROOT)}: missing {marker!r}")

    for path, text in texts.items():
        for asset in DIAGNOSTIC_ASSET_RE.findall(text):
            if asset not in ALLOWED_RELEASE_ASSETS:
                failures.append(
                    f"{path.relative_to(ROOT)}: unsupported diagnostic asset {asset!r}"
                )

    if failures:
        raise SystemExit(
            "Public diagnostic documentation verification failed:\n- "
            + "\n- ".join(failures)
        )

    print("Public diagnostic documentation verification passed.")


def main() -> None:
    verify()


if __name__ == "__main__":
    main()
