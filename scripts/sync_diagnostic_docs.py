#!/usr/bin/env python3
"""Verify the public diagnostic documentation.

Public distribution is intentionally limited to:
- TSUN-Local-Diagnostic.exe for Windows x86_64;
- TSUN-Local-Diagnostic-Python.zip for Windows, macOS and Linux with Python 3.10+.

The website and README are maintained directly. This helper is deliberately a
validator rather than a document rewriter so automation cannot restore obsolete
native macOS/Linux download copy.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WINDOWS_ASSET = "TSUN-Local-Diagnostic.exe"
PYTHON_ASSET = "TSUN-Local-Diagnostic-Python.zip"

PUBLIC_FILES = (
    ROOT / "README.md",
    ROOT / "docs" / "index.html",
    ROOT / "docs" / "test-your-inverter.html",
)

FORBIDDEN_NATIVE_ASSETS = (
    "TSUN-Local-Diagnostic-macOS-arm64.zip",
    "TSUN-Local-Diagnostic-macOS-x86_64.zip",
    "TSUN-Local-Diagnostic-Linux-x86_64",
    "TSUN-Local-Diagnostic-Linux-arm64",
)


def verify() -> None:
    """Fail when public documentation drifts from the supported distribution."""
    texts = {path: path.read_text(encoding="utf-8") for path in PUBLIC_FILES}

    readme = texts[ROOT / "README.md"]
    homepage = texts[ROOT / "docs" / "index.html"]
    test_page = texts[ROOT / "docs" / "test-your-inverter.html"]

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
            "Mac &amp; Linux diagnostic →",
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

    failures: list[str] = []
    for path, markers in required.items():
        text = texts[path]
        for marker in markers:
            if marker not in text:
                failures.append(f"{path.relative_to(ROOT)}: missing {marker!r}")

    for path, text in texts.items():
        for asset in FORBIDDEN_NATIVE_ASSETS:
            if asset in text:
                failures.append(
                    f"{path.relative_to(ROOT)}: obsolete public native asset {asset!r}"
                )

    if "no separate official macOS or Linux native binaries" not in readme:
        failures.append("README.md: missing explicit native-package clarification")
    if "no separate official native Mac or Linux binary" not in homepage:
        failures.append("docs/index.html: missing cross-platform Python clarification")
    if "no separate official native macOS or Linux binaries" not in test_page:
        failures.append("docs/test-your-inverter.html: missing package clarification")

    if failures:
        raise SystemExit("Public diagnostic documentation verification failed:\n- " + "\n- ".join(failures))

    print("Public diagnostic documentation verification passed.")


def main() -> None:
    verify()


if __name__ == "__main__":
    main()
