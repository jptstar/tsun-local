#!/usr/bin/env python3
"""Make desktop-download choices and macOS Gatekeeper guidance unambiguous.

This deliberately keeps every existing release URL and documentation path
unchanged so old forum/HACF links continue to work.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

MAC_APPLE_LABEL = "Mac M1 / M2 / M3 / M4… (Apple Silicon)"
MAC_INTEL_LABEL = "Mac Intel (older Macs)"


def write_if_changed(path: Path, text: str) -> None:
    old = path.read_text(encoding="utf-8")
    if text != old:
        path.write_text(text, encoding="utf-8")


def replace_all(path: Path, replacements: tuple[tuple[str, str], ...]) -> None:
    text = path.read_text(encoding="utf-8")
    for old, new in replacements:
        text = text.replace(old, new)
    write_if_changed(path, text)


def clarify_markdown_platform_labels() -> None:
    paths = [
        ROOT / "README.md",
        ROOT / "tools" / "README.md",
        DOCS / "HARDWARE_DUMP.md",
        DOCS / "DIRECT_DIAGNOSTIC_UPLOAD_TEST.md",
        *sorted(DOCS.glob("README_*.md")),
    ]
    replacements = (
        ("macOS Apple Silicon", f"macOS — {MAC_APPLE_LABEL}"),
        ("macOS Intel", f"macOS — {MAC_INTEL_LABEL}"),
    )
    for path in paths:
        replace_all(path, replacements)


def clarify_french_readme() -> None:
    path = DOCS / "README_FR.md"
    text = path.read_text(encoding="utf-8")
    text = text.replace("macOS — Mac Intel (older Macs)", "macOS — Mac Intel (anciens Mac)")

    chooser = (
        "> **Quel Mac choisir ?**  \n"
        "> • **Mac avec une puce Apple M1, M2, M3, M4 ou plus récente** → choisissez **Mac M1 / M2 / M3 / M4… (Apple Silicon)**.  \n"
        "> • **Mac dont  → À propos de ce Mac indique Intel** → choisissez **Mac Intel**.\n\n"
    )
    if "> **Quel Mac choisir ?**" not in text:
        text = re.sub(
            r"(\| Linux arm64 .*?\|\n\n)(Versions actuelles :)",
            rf"\1{chooser}\2",
            text,
            count=1,
        )

    text = re.sub(
        r"Sous macOS, l’application (?:est signée de manière ad hoc mais pas encore notarifiée Apple :|n’est \*\*pas encore notarifiée par Apple\*\*\.).*?(?=Sous Linux,)",
        (
            "Sous macOS, l’application n’est **pas encore notarifiée par Apple**. "
            "Si l’alerte **« Apple n’a pas pu confirmer que TSUN Local Diagnostic ne contenait pas de logiciel malveillant »** apparaît, "
            "cliquez **Terminé**, puis ouvrez ** → Réglages Système → Confidentialité et sécurité**, faites défiler jusqu’à **Sécurité**, "
            "cliquez **Ouvrir quand même**, authentifiez-vous puis confirmez **Ouvrir**. "
            "Apple indique que cette option reste disponible environ une heure après la tentative d’ouverture. "
            "Si macOS indique au contraire que l’app **« endommagera votre Mac »** ou détecte explicitement un logiciel malveillant, "
            "**ne contournez pas l’alerte**. "
            "[Procédure Apple officielle](https://support.apple.com/fr-fr/guide/mac-help/mh40616/mac). "
        ),
        text,
        count=1,
        flags=re.DOTALL,
    )
    write_if_changed(path, text)


def clarify_english_markdown() -> None:
    chooser = (
        "> **Which Mac should I download?**  \n"
        "> • **Apple chip M1, M2, M3, M4 or newer** → choose **Mac M1 / M2 / M3 / M4… (Apple Silicon)**.  \n"
        "> • **About This Mac says Intel** → choose **Mac Intel**.\n\n"
    )

    for path in (ROOT / "README.md", ROOT / "tools" / "README.md", DOCS / "HARDWARE_DUMP.md"):
        text = path.read_text(encoding="utf-8")
        if "> **Which Mac should I download?**" not in text:
            anchor_patterns = (
                r"(\| \*\*Linux arm64\*\* .*?\|\n\n)",
                r"(\| Linux arm64 .*?\|\n\n)",
            )
            for pattern in anchor_patterns:
                updated, count = re.subn(pattern, rf"\1{chooser}", text, count=1)
                if count:
                    text = updated
                    break

        text = re.sub(
            r"The macOS (?:application|applications|packages) (?:is|are) (?:currently )?ad-hoc signed but (?:(?:is|are) )?not (?:currently )?Apple-notarized\..*?(?=\n\n|On Linux|Linux downloads)",
            (
                "The macOS packages are ad-hoc signed but **not yet notarized by Apple**. "
                "If macOS says **“Apple cannot verify that this app is free of malware”**, click **Done**, then open "
                "**Apple menu → System Settings → Privacy & Security**, scroll to **Security**, click **Open Anyway**, authenticate, "
                "then confirm **Open**. Apple says this override is available for about one hour after the failed launch attempt. "
                "If macOS instead says the app **will damage your Mac** or explicitly reports malware, **do not bypass that warning**. "
                "See [Apple’s official instructions](https://support.apple.com/en-gb/102445). "
            ),
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
        ">Mac M1 / M2 / M3 / M4… (Apple Silicon)<",
    ).replace(
        ">macOS Intel<",
        ">Mac Intel (older Macs)<",
    )

    old_block = re.compile(
        r'<div class="privacy"><strong>macOS first launch:</strong>.*?</div>',
        re.DOTALL,
    )
    new_block = (
        '<div class="privacy"><strong>macOS first launch:</strong> these packages are ad-hoc signed but <strong>not yet notarized by Apple</strong>. '
        'If you see <strong>“Apple cannot verify that TSUN Local Diagnostic is free of malware”</strong>, click <strong>Done</strong>. '
        'Then open <strong>Apple menu → System Settings → Privacy &amp; Security</strong>, scroll to <strong>Security</strong>, '
        'click <strong>Open Anyway</strong>, authenticate, then confirm <strong>Open</strong>. Apple says this option is available for about one hour after the failed launch attempt. '
        'If macOS instead says the app <strong>will damage your Mac</strong> or explicitly reports malware, <strong>do not bypass the warning</strong>. '
        '<a href="https://support.apple.com/en-gb/102445">Apple official instructions</a>.</div>'
    )
    text = old_block.sub(new_block, text, count=1)

    if "Which Mac should I download?" not in text:
        marker = '<div class="actions">'
        chooser = (
            '<div class="privacy"><strong>Which Mac should I download?</strong> '
            'Mac with an Apple chip <strong>M1, M2, M3, M4 or newer</strong> → choose <strong>Apple Silicon</strong>. '
            'If <strong>Apple menu → About This Mac</strong> says <strong>Intel</strong> → choose <strong>Mac Intel</strong>.</div>\n    '
        )
        text = text.replace(marker, chooser + marker, 1)

    write_if_changed(path, text)


def clarify_homepage_card() -> None:
    path = DOCS / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "<strong>macOS &amp; Linux diagnostic →</strong><span class=\"muted\">The same TSUN Local Diagnostic interface is now packaged for Apple Silicon, Intel, Linux x86_64 and Linux arm64.</span>",
        "<strong>Mac &amp; Linux diagnostic →</strong><span class=\"muted\">Mac M1/M2/M3/M4… uses Apple Silicon; older Intel Macs use the Intel package. Linux packages are available for Intel/AMD and ARM64.</span>",
    )
    write_if_changed(path, text)


def main() -> None:
    clarify_markdown_platform_labels()
    clarify_french_readme()
    clarify_english_markdown()
    clarify_test_page()
    clarify_homepage_card()
    print("Clarified Mac model selection and current Gatekeeper instructions.")


if __name__ == "__main__":
    main()
