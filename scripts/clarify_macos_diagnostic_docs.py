#!/usr/bin/env python3
"""Keep desktop diagnostic documentation safe and unambiguous.

Windows/Linux downloads remain public. macOS public downloads are intentionally
paused until Developer ID signing and Apple notarization are active. The stable
macOS filenames are preserved so the same URLs can be restored once notarized.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

MAC_APPLE_LABEL = "Mac M1 / M2 / M3 / M4… (Apple Silicon)"
MAC_INTEL_LABEL = "Mac Intel (older Macs)"
MAC_ARM_ASSET = "TSUN-Local-Diagnostic-macOS-arm64.zip"
MAC_INTEL_ASSET = "TSUN-Local-Diagnostic-macOS-x86_64.zip"


def write_if_changed(path: Path, text: str) -> None:
    old = path.read_text(encoding="utf-8")
    if text != old:
        path.write_text(text, encoding="utf-8")


def replace_all(path: Path, replacements: tuple[tuple[str, str], ...]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    write_if_changed(path, text)


def markdown_paths() -> list[Path]:
    return [
        ROOT / "README.md",
        ROOT / "tools" / "README.md",
        DOCS / "HARDWARE_DUMP.md",
        DOCS / "DIRECT_DIAGNOSTIC_UPLOAD_TEST.md",
        *sorted(DOCS.glob("README_*.md")),
    ]


def clarify_platform_labels() -> None:
    replacements = (
        ("macOS Apple Silicon", f"macOS — {MAC_APPLE_LABEL}"),
        ("macOS Intel", f"macOS — {MAC_INTEL_LABEL}"),
    )
    for path in markdown_paths():
        replace_all(path, replacements)


def pause_public_macos_markdown_downloads() -> None:
    for path in markdown_paths():
        text = path.read_text(encoding="utf-8")
        french = path.name == "README_FR.md"
        status = (
            "**Téléchargement public suspendu — validation Apple en cours**"
            if french
            else "**Public download paused — Apple notarization in progress**"
        )
        intel_label = "Mac Intel (anciens Mac)" if french else MAC_INTEL_LABEL
        apple_row = f"| macOS — {MAC_APPLE_LABEL} | {status} | — |"
        intel_row = f"| macOS — {intel_label} | {status} | — |"
        text = re.sub(
            rf"^\|.*{re.escape(MAC_ARM_ASSET)}.*\|$",
            apple_row,
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            rf"^\|.*{re.escape(MAC_INTEL_ASSET)}.*\|$",
            intel_row,
            text,
            flags=re.MULTILINE,
        )
        write_if_changed(path, text)


def clarify_french_readme() -> None:
    path = DOCS / "README_FR.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("macOS — Mac Intel (older Macs)", "macOS — Mac Intel (anciens Mac)")

    chooser = (
        "> **Quel Mac choisir lorsque les builds signés seront publiés ?**  \n"
        "> • **Mac avec une puce Apple M1, M2, M3, M4 ou plus récente** → **Apple Silicon**.  \n"
        "> • **Mac dont  → À propos de ce Mac indique Intel** → **Mac Intel**.\n\n"
    )
    text = re.sub(
        r"> \*\*Quel Mac choisir.*?(?=Versions actuelles :)",
        chooser,
        text,
        count=1,
        flags=re.DOTALL,
    )

    paused = (
        "Sous macOS, les téléchargements publics sont **temporairement suspendus pendant la mise en place de la signature Developer ID et de la notarisation Apple**. "
        "Nous préférons ne pas demander aux utilisateurs de contourner les protections de macOS. "
        "Les mêmes noms de fichiers et les mêmes URL stables seront réutilisés dès que les paquets notarifiés seront disponibles. "
    )
    text = re.sub(
        r"Sous macOS,.*?(?=Sous Linux,)",
        paused,
        text,
        count=1,
        flags=re.DOTALL,
    )
    write_if_changed(path, text)


def clarify_english_markdown() -> None:
    chooser = (
        "> **Which Mac should I download once the signed builds are published?**  \n"
        "> • **Apple chip M1, M2, M3, M4 or newer** → **Apple Silicon**.  \n"
        "> • **About This Mac says Intel** → **Mac Intel**.\n\n"
    )

    for path in (ROOT / "README.md", ROOT / "tools" / "README.md", DOCS / "HARDWARE_DUMP.md"):
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"> \*\*Which Mac should I download.*?(?=(?:\*\*Current|Current standalone|All packages|### Updates))",
            chooser,
            text,
            count=1,
            flags=re.DOTALL,
        )
        paused = (
            "macOS public downloads are **temporarily paused while Developer ID signing and Apple notarization are enabled**. "
            "We do not want ordinary users to be asked to bypass macOS security protections. "
            "The same stable filenames and URLs will be restored as soon as the notarized packages are available. "
        )
        text = re.sub(
            r"The macOS (?:application|applications|packages).*?(?=On Linux|Linux downloads|\n\nThe dump engine)",
            paused,
            text,
            count=1,
            flags=re.DOTALL,
        )
        write_if_changed(path, text)


def clarify_test_page() -> None:
    path = DOCS / "test-your-inverter.html"
    text = path.read_text(encoding="utf-8")

    text = text.replace(
        ">macOS Apple Silicon<",
        f">{MAC_APPLE_LABEL}<",
    ).replace(
        ">macOS Intel<",
        f">{MAC_INTEL_LABEL}<",
    )

    text = re.sub(
        rf'<a class="button secondary" href="https://github\.com/jptstar/tsun-local/releases/download/diagnostic-latest/{re.escape(MAC_ARM_ASSET)}">.*?</a>',
        f'<span class="button secondary" aria-disabled="true">{MAC_APPLE_LABEL} — Apple validation in progress</span>',
        text,
        count=1,
    )
    text = re.sub(
        rf'<a class="button secondary" href="https://github\.com/jptstar/tsun-local/releases/download/diagnostic-latest/{re.escape(MAC_INTEL_ASSET)}">.*?</a>',
        f'<span class="button secondary" aria-disabled="true">{MAC_INTEL_LABEL} — Apple validation in progress</span>',
        text,
        count=1,
    )

    chooser = (
        '<div class="privacy"><strong>Which Mac will I need?</strong> '
        'Mac with an Apple chip <strong>M1, M2, M3, M4 or newer</strong> → <strong>Apple Silicon</strong>. '
        'If <strong>Apple menu → About This Mac</strong> says <strong>Intel</strong> → <strong>Mac Intel</strong>.</div>'
    )
    text = re.sub(
        r'<div class="privacy"><strong>Which Mac should I download\?</strong>.*?</div>',
        chooser,
        text,
        count=1,
        flags=re.DOTALL,
    )

    paused = (
        '<div class="privacy"><strong>macOS availability:</strong> public Mac downloads are temporarily paused while '
        '<strong>Developer ID signing and Apple notarization</strong> are enabled. We prefer not to ask ordinary users to bypass '
        'macOS security protections. The same stable package names and URLs will return once notarized builds are ready.</div>'
    )
    text = re.sub(
        r'<div class="privacy"><strong>macOS first launch:</strong>.*?</div>',
        paused,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if "macOS availability:" not in text:
        marker = '<div class="privacy"><strong>Linux first launch:'
        text = text.replace(marker, paused + "\n    " + marker, 1)

    write_if_changed(path, text)


def clarify_homepage_card() -> None:
    path = DOCS / "index.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'<a class="card" style="display:block;color:inherit;text-decoration:none" href="test-your-inverter\.html"><strong>Mac &amp; Linux diagnostic →</strong><span class="muted">.*?</span></a>',
        '<a class="card" style="display:block;color:inherit;text-decoration:none" href="test-your-inverter.html"><strong>Mac &amp; Linux diagnostic →</strong><span class="muted">Linux packages are available now. Mac packages keep the same interface but public download is paused until Apple-notarized builds are ready.</span></a>',
        text,
        count=1,
        flags=re.DOTALL,
    )
    write_if_changed(path, text)


def main() -> None:
    clarify_platform_labels()
    pause_public_macos_markdown_downloads()
    clarify_french_readme()
    clarify_english_markdown()
    clarify_test_page()
    clarify_homepage_card()
    print("Paused public macOS downloads pending Developer ID signing and notarization.")


if __name__ == "__main__":
    main()
