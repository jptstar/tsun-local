#!/usr/bin/env python3
"""Publish clear macOS download links and first-launch guidance.

The public Mac packages are ad-hoc signed when Apple Developer ID notarization is
not configured. Gatekeeper may therefore block the first launch. Documentation
must explain the per-application "Open Anyway" procedure without asking users to
disable Gatekeeper globally.
"""

from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

MAC_APPLE_LABEL = "Mac M1 / M2 / M3 / M4… (Apple Silicon)"
MAC_INTEL_LABEL = "Mac Intel (older Macs)"
MAC_ARM = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-arm64.zip"
MAC_INTEL = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-x86_64.zip"


def write_if_changed(path: Path, text: str) -> None:
    old = path.read_text(encoding="utf-8")
    if text != old:
        path.write_text(text, encoding="utf-8")


def markdown_paths() -> list[Path]:
    return [
        ROOT / "README.md",
        ROOT / "tools" / "README.md",
        DOCS / "HARDWARE_DUMP.md",
        DOCS / "DIRECT_DIAGNOSTIC_UPLOAD_TEST.md",
        *sorted(DOCS.glob("README_*.md")),
    ]


def restore_macos_download_rows() -> None:
    for path in markdown_paths():
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"^\|.*Mac M1 / M2 / M3 / M4.*\|$",
            f"| macOS — {MAC_APPLE_LABEL} | [TSUN-Local-Diagnostic-macOS-arm64.zip]({MAC_ARM}) | [SHA-256]({MAC_ARM}.sha256) |",
            text,
            flags=re.MULTILINE,
        )
        text = re.sub(
            r"^\|.*Mac Intel.*\|$",
            f"| macOS — {MAC_INTEL_LABEL} | [TSUN-Local-Diagnostic-macOS-x86_64.zip]({MAC_INTEL}) | [SHA-256]({MAC_INTEL}.sha256) |",
            text,
            flags=re.MULTILINE,
        )
        write_if_changed(path, text)


def update_french_readme() -> None:
    path = DOCS / "README_FR.md"
    text = path.read_text(encoding="utf-8")
    warning = (
        "> ### 🟠 Mac — à lire avant le premier lancement\n"
        "> **TSUN Local Diagnostic n’est pas encore notarifié par Apple.** macOS peut donc bloquer le premier lancement.  \n"
        "> **Il n’est pas nécessaire de désactiver la sécurité du Mac ni Gatekeeper.**  \n"
        "> 1. Téléchargez et décompressez le ZIP correspondant à votre Mac.  \n"
        "> 2. Essayez d’ouvrir **TSUN Local Diagnostic.app** une première fois.  \n"
        "> 3. Si macOS bloque l’application, cliquez sur **Terminé**.  \n"
        "> 4. Ouvrez ** → Réglages Système → Confidentialité et sécurité**.  \n"
        "> 5. Dans **Sécurité**, cliquez sur **Ouvrir quand même** pour TSUN Local Diagnostic.  \n"
        "> 6. Authentifiez-vous puis confirmez **Ouvrir**.  \n"
        "> 🟢 Une fois l’application ouverte, c’est terminé : l’exception concerne uniquement TSUN Local Diagnostic et les protections générales de macOS restent actives.\n\n"
    )
    text = re.sub(
        r"> ### 🟠 Mac — à lire avant le premier lancement.*?(?=Versions actuelles :)",
        "",
        text,
        flags=re.DOTALL,
    )
    marker = "Versions actuelles :"
    if marker in text:
        text = text.replace(marker, warning + marker, 1)
    text = re.sub(
        r"Sous macOS, les téléchargements publics.*?(?=Sous Linux,)",
        "Sous macOS, les paquets publics sont disponibles pour Apple Silicon et Intel. Le premier lancement peut nécessiter l’autorisation **Ouvrir quand même** décrite ci-dessus. Ne désactivez jamais Gatekeeper globalement. ",
        text,
        count=1,
        flags=re.DOTALL,
    )
    write_if_changed(path, text)


def update_english_markdown() -> None:
    warning = (
        "> ### 🟠 macOS — read this before the first launch\n"
        "> **TSUN Local Diagnostic is not yet notarized by Apple.** macOS may block the first launch.  \n"
        "> **Do not disable Gatekeeper or Mac security globally.**  \n"
        "> 1. Download and unzip the package for your Mac.  \n"
        "> 2. Try to open **TSUN Local Diagnostic.app** once.  \n"
        "> 3. If macOS blocks it, click **Done**.  \n"
        "> 4. Open **Apple menu → System Settings → Privacy & Security**.  \n"
        "> 5. In **Security**, click **Open Anyway** for TSUN Local Diagnostic.  \n"
        "> 6. Authenticate, then confirm **Open**.  \n"
        "> 🟢 Once the app opens, the exception applies only to TSUN Local Diagnostic; normal macOS protections remain enabled.\n\n"
    )
    for path in (ROOT / "README.md", ROOT / "tools" / "README.md", DOCS / "HARDWARE_DUMP.md"):
        text = path.read_text(encoding="utf-8")
        text = re.sub(
            r"> ### 🟠 macOS — read this before the first launch.*?(?=(?:\*\*Current|Current standalone|All packages|### Updates))",
            "",
            text,
            flags=re.DOTALL,
        )
        markers = ["**Current", "Current standalone", "All packages", "### Updates"]
        for marker in markers:
            if marker in text:
                text = text.replace(marker, warning + marker, 1)
                break
        text = re.sub(
            r"macOS public downloads are \*\*temporarily paused.*?(?=On Linux|Linux downloads|\n\nThe dump engine)",
            "macOS public packages are available for Apple Silicon and Intel. The first launch can require the per-application **Open Anyway** procedure above; never disable Gatekeeper globally. ",
            text,
            count=1,
            flags=re.DOTALL,
        )
        write_if_changed(path, text)


def update_test_page() -> None:
    path = DOCS / "test-your-inverter.html"
    text = path.read_text(encoding="utf-8")

    if ".mac-warning{" not in text:
        text = text.replace(
            ".privacy{margin-top:20px;padding:18px;border-radius:16px;background:#f8fafd;border:1px solid var(--line)}",
            ".privacy{margin-top:20px;padding:18px;border-radius:16px;background:#f8fafd;border:1px solid var(--line)}\n    .mac-warning{margin-top:20px;padding:20px;border:2px solid #e6a31a;border-radius:16px;background:var(--amber-soft);color:#6e4300}\n    .mac-warning strong{display:block;font-size:20px;margin-bottom:8px}.mac-warning p{margin:7px 0}.mac-warning ol{margin:10px 0 0;padding-left:24px}",
            1,
        )

    text = re.sub(r'\n\s*<div class="mac-warning">.*?</div>', "", text, flags=re.DOTALL)
    text = re.sub(r'\n\s*<div class="privacy"><strong>macOS availability:</strong>.*?</div>', "", text, flags=re.DOTALL)

    warning = (
        '<div class="mac-warning"><strong>🟠 macOS — read this before the first launch</strong>'
        '<p><strong>TSUN Local Diagnostic is not yet notarized by Apple.</strong> macOS may block the first launch. '
        '<strong>You do not need to disable Mac security or Gatekeeper.</strong></p>'
        '<ol><li>Download and unzip the package for your Mac.</li>'
        '<li>Try to open <strong>TSUN Local Diagnostic.app</strong> once.</li>'
        '<li>If macOS blocks it, click <strong>Done</strong>.</li>'
        '<li>Open <strong>Apple menu → System Settings → Privacy &amp; Security</strong>.</li>'
        '<li>In <strong>Security</strong>, click <strong>Open Anyway</strong> for TSUN Local Diagnostic.</li>'
        '<li>Authenticate, then confirm <strong>Open</strong>.</li></ol>'
        '<p><strong>🟢 Once the application opens, you are done.</strong> The exception applies only to TSUN Local Diagnostic; normal macOS protections remain enabled.</p></div>'
    )
    chooser_pattern = r'(<div class="privacy"><strong>Which Mac will I need\?</strong>.*?</div>)'
    text = re.sub(chooser_pattern, r"\1\n    " + warning, text, count=1, flags=re.DOTALL)

    text = re.sub(
        r'<span class="button secondary" aria-disabled="true">Mac M1 / M2 / M3 / M4… \(Apple Silicon\).*?</span>',
        f'<a class="button secondary" href="{MAC_ARM}">{MAC_APPLE_LABEL}</a>',
        text,
        count=1,
    )
    text = re.sub(
        r'<span class="button secondary" aria-disabled="true">Mac Intel \(older Macs\).*?</span>',
        f'<a class="button secondary" href="{MAC_INTEL}">{MAC_INTEL_LABEL}</a>',
        text,
        count=1,
    )
    write_if_changed(path, text)


def update_homepage() -> None:
    path = DOCS / "index.html"
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'(<a class="card" style="display:block;color:inherit;text-decoration:none" href="test-your-inverter\.html"><strong>Mac &amp; Linux diagnostic →</strong><span class="muted">).*?(</span></a>)',
        r'\1Mac and Linux packages are available. On Mac, read the first-launch Gatekeeper instructions before downloading; no global security disable is required.\2',
        text,
        count=1,
        flags=re.DOTALL,
    )
    write_if_changed(path, text)


def main() -> None:
    restore_macos_download_rows()
    update_french_readme()
    update_english_markdown()
    update_test_page()
    update_homepage()
    print("Published Mac download links with safe per-application first-launch instructions.")


if __name__ == "__main__":
    main()
