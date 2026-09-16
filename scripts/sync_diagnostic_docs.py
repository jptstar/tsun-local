#!/usr/bin/env python3
"""Keep TSUN Local public diagnostic docs aligned with Windows + full Python."""
from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WIN = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe"
PYZIP = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip"
RELEASE = "https://github.com/jptstar/tsun-local/releases/tag/diagnostic-latest"

def version(path: str, name: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    match = re.search(rf'^\s*{re.escape(name)}\s*=\s*["\']([^"\']+)', text, re.MULTILINE)
    if not match:
        raise RuntimeError(f"Unable to read {name} from {path}")
    return match.group(1)

APP_VERSION = version("tools/tsun_diagnostic_version.py", "APP_VERSION")
DUMP_VERSION = version("tools/tsun_dump.py", "TOOL_VERSION")

def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")

def write(path: str, text: str) -> None:
    (ROOT / path).write_text(text, encoding="utf-8")

def replace_between(text: str, start: str, end: str, replacement: str) -> str:
    a = text.find(start)
    if a < 0:
        raise RuntimeError(f"Missing start marker: {start}")
    b = text.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f"Missing end marker: {end}")
    return text[:a] + replacement.rstrip() + "\n\n" + text[b:]

README_BLOCK = f'''## 🔬 Validate another TSUN model

TSUN Local provides a privacy-safe, **strictly read-only** diagnostic for unlisted models and communication issues. There are now exactly **two supported distributions**, both using the same diagnostic engine, the same ordered 1097/Tuya extensions, the same privacy checks and the same retrying report uploader.

### Windows x86_64

**⬇️ [Download TSUN-Local-Diagnostic.exe]({WIN})** · **[SHA-256]({WIN}.sha256)**

The Windows application is the simplest option for most users. It includes the complete diagnostic runtime and the pinned Tuya backend.

### Full Python package

**⬇️ [Download TSUN-Local-Diagnostic-Python.zip]({PYZIP})** · **[SHA-256]({PYZIP}.sha256)**

The full Python package is the supported route for **Linux** and advanced users. It uses the same runtime as Windows. Python **3.10+** is required.

```bash
python -m pip install -r requirements.txt
python tsun_diagnostic_cli.py --full
```

**Current diagnostic versions:** application **{APP_VERSION}** · dump engine **{DUMP_VERSION}**.

> [!IMPORTANT]
> `tsun_dump.py` remains available only as a minimal compatibility tool. For complete diagnostics, including the current 1097/Tuya extensions and canonical upload retry/privacy path, use the Windows executable or the full Python package above.

The diagnostic workflow is the same in both supported distributions:

1. **Disable TSUN Local** for the affected logger.
2. **Run the diagnostic**.
3. **Direct report upload** — recommended; explicit consent is mandatory.
4. **Manual e-mail report** — optional fallback only.

Reports stay local if upload fails. Transient network failures are retried automatically, while privacy validation is performed before any transmission.

**📦 [Open the rolling diagnostic release]({RELEASE})** · 📚 **[Hardware Validation Dump Tool guide](docs/HARDWARE_DUMP.md)** · 📋 **[Diagnostic upload validation protocol](docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · 🌐 **[Test your inverter](https://jptstar.github.io/tsun-local/test-your-inverter.html)**
'''

FR_BLOCK = f'''## 🔬 Valider un autre modèle TSUN

TSUN Local propose un diagnostic respectueux de la vie privée et **strictement en lecture seule** pour les modèles non listés et les problèmes de communication. Il existe désormais exactement **deux distributions prises en charge**, utilisant le même moteur, les mêmes extensions 1097/Tuya, les mêmes contrôles de confidentialité et le même envoi avec nouvelles tentatives automatiques.

### Windows x86_64

**⬇️ [Télécharger TSUN-Local-Diagnostic.exe]({WIN})** · **[SHA-256]({WIN}.sha256)**

L'application Windows est l'option la plus simple pour la majorité des utilisateurs et contient le diagnostic complet.

### Package Python complet

**⬇️ [Télécharger TSUN-Local-Diagnostic-Python.zip]({PYZIP})** · **[SHA-256]({PYZIP}.sha256)**

Le package Python complet est la solution prise en charge pour **Linux** et les utilisateurs avancés. Il utilise le même runtime que Windows. Python **3.10+** est requis.

```bash
python -m pip install -r requirements.txt
python tsun_diagnostic_cli.py --full
```

**Versions actuelles du diagnostic :** application **{APP_VERSION}** · moteur de dump **{DUMP_VERSION}**.

> [!IMPORTANT]
> `tsun_dump.py` reste disponible uniquement comme outil minimal de compatibilité. Pour le diagnostic complet, y compris les extensions 1097/Tuya actuelles et l'envoi canonique avec retry/confidentialité, utilisez l'EXE Windows ou le package Python complet.

Le déroulement est identique dans les deux distributions :

1. **Désactiver TSUN Local** pour le logger concerné.
2. **Lancer le diagnostic**.
3. **Envoi direct du rapport** — recommandé, avec consentement explicite obligatoire.
4. **Envoi manuel par e-mail** — uniquement en secours.

En cas d'échec d'envoi, les rapports restent enregistrés localement. Les erreurs réseau transitoires sont réessayées automatiquement et le contrôle de confidentialité a lieu avant toute transmission.

**📦 [Ouvrir la release diagnostic]({RELEASE})** · 📚 **[Guide du diagnostic matériel](HARDWARE_DUMP.md)** · 📋 **[Protocole de validation de l'envoi](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · 🌐 **[Tester votre onduleur](https://jptstar.github.io/tsun-local/test-your-inverter.html)**
'''

text = read("README.md")
text = replace_between(text, "## 🔬 Validate another TSUN model", "### Sunology PLAY2", README_BLOCK)
write("README.md", text)

text = read("docs/README_FR.md")
text = replace_between(text, "## 🔬 Valider un autre modèle TSUN", "### Sunology PLAY2", FR_BLOCK)
write("docs/README_FR.md", text)

tools_block = f'''## Diagnostic distributions — Windows and Python

TSUN Local maintains exactly two supported diagnostic distributions. Both use the same privacy-safe, **strictly read-only** hardware engine and the same ordered 1097/Tuya runtime.

| Distribution | Download | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [checksum]({WIN}.sha256) |
| Full Python package | [TSUN-Local-Diagnostic-Python.zip]({PYZIP}) | [checksum]({PYZIP}.sha256) |

**Versions:** application **{APP_VERSION}** · dump engine **{DUMP_VERSION}**.

Windows is the recommended end-user package. Linux users use the full Python package:

```bash
python -m pip install -r requirements.txt
python tsun_diagnostic_cli.py --full
```

The historical single-file `tsun_dump.py` remains available for compatibility, but it is not the feature-parity distribution.

📋 [Diagnostic/direct-upload validation protocol](../docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)
'''
text = read("tools/README.md")
text = replace_between(text, "## Desktop diagnostic —", "## Hardware validation dump", tools_block)
text = text.replace("The desktop packages above are the recommended route for end users.", "The Windows executable and full Python package above are the recommended diagnostic routes.")
text = re.sub(r'Dump engine \*\*[0-9.]+\*\*', f'Dump engine **{DUMP_VERSION}**', text)
write("tools/README.md", text)

# Keep distribution wording in validation docs current without rewriting their protocol details.
for path in ("docs/HARDWARE_DUMP.md", "docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md"):
    text = read(path)
    text = text.replace("launch the desktop diagnostic for the current operating system", "launch the Windows diagnostic or the full Python package")
    text = text.replace("All desktop packages and the Python dumper are published", "The Windows executable and full Python package are published")
    text = text.replace("desktop packages", "supported diagnostic packages")
    text = text.replace("Python dumper", "full Python diagnostic")
    write(path, text)

# Homepage SEO: retain the strong Home Assistant query while adding the diagnostic entry points.
path = "docs/index.html"
text = read(path)
text = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="Open-source, local and read-only Home Assistant integration for TSUN microinverters. HACS install, clear-text alarms, no cloud or proxy, plus read-only Windows and Python diagnostics for hardware validation.">', text, count=1)
text = re.sub(r'<meta name="keywords" content="[^"]*">', '<meta name="keywords" content="TSUN Local, TSUN Home Assistant, TSUN microinverter, Home Assistant TSUN integration, HACS, TSUN diagnostic, TSUN Local Diagnostic, Windows diagnostic, Python diagnostic, TSOL-MS300, TSOL-MP3000, TSOL-MX500, TSOL-MS800, TSOL-MS2000, Sunology PLAY2, 1511, 02B0, 1097, local solar monitoring">', text, count=1)
text = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="Local, read-only TSUN microinverter monitoring for Home Assistant plus Windows and Python diagnostics for compatibility testing. HACS install, no cloud, no proxy.">', text, count=1)
text = re.sub(r'<meta name="twitter:description" content="[^"]*">', '<meta name="twitter:description" content="TSUN microinverters in Home Assistant: local, read-only, HACS, no cloud or proxy, with Windows and Python diagnostics.">', text, count=1)
if '"name":"TSUN Local Diagnostic"' not in text:
    text = text.replace('\n    ]\n  }\n  </script>', f''',\n      {{"@type":"SoftwareApplication","name":"TSUN Local Diagnostic","softwareVersion":"{APP_VERSION}","applicationCategory":"UtilitiesApplication","operatingSystem":"Windows; Python 3.10+ on Linux","url":"https://jptstar.github.io/tsun-local/test-your-inverter.html","downloadUrl":"{RELEASE}","isAccessibleForFree":true,"description":"Strictly read-only TSUN microinverter hardware diagnostic distributed as a Windows executable and full Python package."}}\n    ]\n  }}\n  </script>''', 1)
# Remove the obsolete third diagnostic card if it still exists.
text = re.sub(r'\s*<a class="card"[^>]*>\s*<strong>Mac &amp; Linux diagnostic →</strong>.*?</a>', '', text, count=1, flags=re.DOTALL)
write(path, text)

# Public compatibility-test page: current distribution + search/social metadata.
path = "docs/test-your-inverter.html"
text = read(path)
text = re.sub(r'<title>.*?</title>', '<title>TSUN Microinverter Compatibility Test for Home Assistant | TSUN Local</title>', text, count=1)
text = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="Test an unlisted TSUN microinverter locally with TSUN Local Diagnostic. Use the Windows executable or full Python package; strictly read-only, no cloud, privacy-safe report upload with explicit consent.">', text, count=1)
text = re.sub(r'<meta name="keywords" content="[^"]*">', '<meta name="keywords" content="TSUN microinverter compatibility, TSUN Home Assistant, TSUN Local Diagnostic, Home Assistant microinverter, Windows diagnostic, Python diagnostic, HACS, TSOL-MP3000, TSOL-MX500, TSOL-MS800, 1511, 02B0, 1097">', text, count=1)
text = re.sub(r'<meta property="og:title" content="[^"]*">', '<meta property="og:title" content="Test your TSUN microinverter with Home Assistant">', text, count=1)
text = re.sub(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="Read-only TSUN Local Diagnostic with two supported distributions: Windows x86_64 and the full Python package for Linux and advanced users.">', text, count=1)
text = re.sub(r'<meta name="twitter:title" content="[^"]*">', '<meta name="twitter:title" content="Test your TSUN microinverter with Home Assistant">', text, count=1)
text = re.sub(r'<meta name="twitter:description" content="[^"]*">', '<meta name="twitter:description" content="Read-only TSUN Local Diagnostic for Windows and full Python, with privacy-safe report upload.">', text, count=1)
text = re.sub(r'"dateModified":"[0-9-]+"', '"dateModified":"2026-09-16"', text, count=1)
text = re.sub(r'"description":"Test whether an unlisted TSUN microinverter[^\"]*"', '"description":"Test an unlisted TSUN microinverter locally with the strictly read-only TSUN Local Diagnostic, available as Windows x86_64 and a full Python package."', text, count=1)
py_section = f'''  <section id="python">
  <h2>Full Python diagnostic — Linux and advanced users</h2>
  <p class="intro">The full Python package uses the same diagnostic engine, ordered 1097/Tuya runtime, privacy validation and retrying uploader as the Windows application. Python 3.10+ is required.</p>
  <div class="actions">
    <a class="button primary" href="{PYZIP}">Download full Python package</a>
    <a class="button secondary" href="{PYZIP}.sha256">SHA-256</a>
  </div>
  <pre class="code">python -m pip install -r requirements.txt
python tsun_diagnostic_cli.py --full</pre>
  <div class="callout"><strong>Linux:</strong> use this package instead of a dedicated Linux executable. <code>tsun_dump.py</code> remains only as a minimal compatibility tool.</div>
</section>'''
text = re.sub(r'  <section id="python">.*?</section>', py_section, text, count=1, flags=re.DOTALL)
write(path, text)

# Sitemap URLs stay stable; refresh lastmod where the sitemap already exposes it.
path = "docs/sitemap.xml"
text = read(path)
for url in ("https://jptstar.github.io/tsun-local/", "https://jptstar.github.io/tsun-local/test-your-inverter.html"):
    text = re.sub(rf'(<loc>{re.escape(url)}</loc>\s*<lastmod>)[^<]+', rf'\g<1>2026-09-16', text)
write(path, text)
