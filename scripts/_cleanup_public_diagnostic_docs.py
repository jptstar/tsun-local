from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WIN = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe"
DUMP = "https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py"
REL = "https://github.com/jptstar/tsun-local/releases/tag/diagnostic-latest"


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def write(rel, text):
    (ROOT / rel).write_text(text, encoding="utf-8")


def replace_section(rel, pattern, replacement):
    text = read(rel)
    text2, n = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError(f"Expected one section in {rel}, got {n}")
    write(rel, text2)


root_section = f'''## 🔬 Validate another TSUN model

TSUN Local provides a privacy-safe, **strictly read-only** diagnostic for unlisted models and communication issues.

### Desktop app — Windows

| Platform | Download | SHA-256 |
|---|---|---|
| **Windows x86_64** | **[TSUN-Local-Diagnostic.exe]({WIN})** | [checksum]({WIN}.sha256) |

**Current public diagnostic versions:** desktop GUI **1.5.12** · dump engine **2.8.3**.

> [!IMPORTANT]
> The rolling tag and historical Windows asset name are deliberately preserved. Older Windows diagnostic links continue to point to the current Windows build.

The Windows desktop interface uses the same **1 → 2 → 3 → 4** flow:

1. **Disable TSUN Local** for the affected logger.
2. **Run the diagnostic**.
3. **Direct report upload** — recommended; explicit consent is mandatory.
4. **Manual e-mail report** — optional fallback only.

The direct-upload dialog can remember the tester name/pseudonym and up to 10 searchable micro-inverter model/quantity rows. The consent checkbox is never remembered. After a successful upload, the application shows the `TSL-...` receipt plus a private-token **Open report** link so the tester can see exactly the anonymized JSON that was submitted.

For an upload-only test away from the installation, use `89:89:89:89` as logger IP and `89898989` as Monitor SN. This mode records that no logger or micro-inverter communication was attempted.

### Python / command-line alternative

**⬇️ [Download `tsun_dump.py`]({DUMP})** — Python 3.10+.  
**🔐 [SHA-256 checksum]({DUMP}.sha256)**

```text
python tsun_dump.py --full
```

**📦 [Open the rolling diagnostic release]({REL})** · 📚 **[Hardware Validation Dump Tool guide](docs/HARDWARE_DUMP.md)** · 📋 **[Desktop/direct-upload validation protocol](docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · 🌐 **[Public test page](https://jptstar.github.io/tsun-local/test-your-inverter.html)**
'''
replace_section("README.md", r"## 🔬 Validate another TSUN model\n.*?(?=\n### Sunology PLAY2)", root_section.rstrip())

localized = {
"docs/README_FR.md": f'''## 🔬 Valider un autre modèle TSUN

TSUN Local propose un diagnostic **strictement en lecture seule** pour les modèles non listés et les problèmes de communication.

### Application de bureau — Windows

| Plateforme | Téléchargement | Contrôle |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [SHA-256]({WIN}.sha256) |

Le parcours Windows suit quatre étapes : désactiver TSUN Local, lancer le diagnostic, envoyer directement le rapport après consentement, ou utiliser l’e-mail uniquement en secours.

### Alternative Python / ligne de commande

[`tsun_dump.py`]({DUMP}) reste disponible avec Python 3.10+ :

```text
python tsun_dump.py --full
```

**[Release diagnostic stable]({REL})** · 📋 **[Protocole de validation](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · 📚 **[Guide du diagnostic matériel](HARDWARE_DUMP.md)**
''',
"docs/README_DE.md": f'''## 🔬 Ein weiteres TSUN-Modell validieren

TSUN Local bietet eine datenschutzfreundliche, **streng schreibgeschützte** Diagnose für nicht aufgeführte Modelle und Kommunikationsprobleme.

### Desktop-Anwendung — Windows

| Plattform | Download | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [SHA-256]({WIN}.sha256) |

Der Windows-Ablauf umfasst vier Schritte: TSUN Local deaktivieren, Diagnose starten, Bericht nach ausdrücklicher Zustimmung direkt hochladen oder E-Mail nur als Fallback verwenden.

### Python-/Kommandozeilen-Alternative

[`tsun_dump.py`]({DUMP}) bleibt für Python 3.10+ verfügbar:

```text
python tsun_dump.py --full
```

**[Stabile Diagnose-Release]({REL})** · **[Validierungsprotokoll](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Hardware-Diagnosehandbuch](HARDWARE_DUMP.md)**
''',
"docs/README_ES.md": f'''## 🔬 Validar otro modelo TSUN

TSUN Local ofrece un diagnóstico **estrictamente de solo lectura** para modelos no listados y problemas de comunicación.

### Aplicación de escritorio — Windows

| Plataforma | Descarga | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [SHA-256]({WIN}.sha256) |

El flujo de Windows tiene cuatro pasos: desactivar TSUN Local, ejecutar el diagnóstico, enviar directamente el informe tras el consentimiento o usar el correo solo como alternativa.

### Alternativa Python / línea de comandos

[`tsun_dump.py`]({DUMP}) sigue disponible con Python 3.10+:

```text
python tsun_dump.py --full
```

**[Release estable del diagnóstico]({REL})** · **[Protocolo de validación](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Guía de diagnóstico](HARDWARE_DUMP.md)**
''',
"docs/README_IT.md": f'''## 🔬 Validare un altro modello TSUN

TSUN Local offre una diagnostica **rigorosamente in sola lettura** per modelli non elencati e problemi di comunicazione.

### App desktop — Windows

| Piattaforma | Download | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [SHA-256]({WIN}.sha256) |

Il flusso Windows usa quattro passaggi: disattivare TSUN Local, eseguire la diagnostica, inviare direttamente il report dopo il consenso oppure usare l’e-mail solo come fallback.

### Alternativa Python / riga di comando

[`tsun_dump.py`]({DUMP}) resta disponibile con Python 3.10+:

```text
python tsun_dump.py --full
```

**[Release diagnostica stabile]({REL})** · **[Protocollo di validazione](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Guida diagnostica](HARDWARE_DUMP.md)**
''',
"docs/README_NL.md": f'''## 🔬 Een ander TSUN-model valideren

TSUN Local biedt een privacyvriendelijke, **strikt alleen-lezen** diagnose voor niet-vermelde modellen en communicatieproblemen.

### Desktop-app — Windows

| Platform | Download | Controle |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [SHA-256]({WIN}.sha256) |

De Windows-workflow heeft vier stappen: TSUN Local uitschakelen, de diagnose uitvoeren, het rapport na toestemming direct uploaden of e-mail alleen als terugvaloptie gebruiken.

### Python-/opdrachtregelalternatief

[`tsun_dump.py`]({DUMP}) blijft beschikbaar voor Python 3.10+:

```text
python tsun_dump.py --full
```

**[Stabiele diagnostic-release]({REL})** · **[Validatieprotocol](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Diagnosehandleiding](HARDWARE_DUMP.md)**
''',
"docs/README_PL.md": f'''## 🔬 Walidacja kolejnego modelu TSUN

TSUN Local udostępnia bezpieczną dla prywatności, **ściśle tylko do odczytu** diagnostykę dla modeli spoza listy i problemów z komunikacją.

### Aplikacja desktopowa — Windows

| Platforma | Pobieranie | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [SHA-256]({WIN}.sha256) |

Proces Windows obejmuje cztery kroki: wyłączyć TSUN Local, uruchomić diagnostykę, bezpośrednio wysłać raport po wyrażeniu zgody albo użyć e-maila tylko jako metody awaryjnej.

### Alternatywa Python / wiersz poleceń

[`tsun_dump.py`]({DUMP}) pozostaje dostępny dla Python 3.10+:

```text
python tsun_dump.py --full
```

**[Stabilne wydanie diagnostyczne]({REL})** · **[Protokół walidacji](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[Przewodnik diagnostyczny](HARDWARE_DUMP.md)**
''',
"docs/README_ZH.md": f'''## 🔬 验证其他 TSUN 型号

TSUN Local 为未列出的型号和通信问题提供隐私安全、**严格只读**的诊断工具。

### 桌面应用 — Windows

| 平台 | 下载 | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [SHA-256]({WIN}.sha256) |

Windows 流程分为四步：禁用对应的 TSUN Local 配置、运行诊断、在明确同意后直接上传报告，或仅在需要时使用电子邮件备用方式。

### Python / 命令行替代方案

[`tsun_dump.py`]({DUMP}) 仍可用于 Python 3.10+：

```text
python tsun_dump.py --full
```

**[稳定诊断版本]({REL})** · **[验证协议](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)** · **[诊断指南](HARDWARE_DUMP.md)**
''',
}
for rel, section in localized.items():
    replace_section(rel, r"## 🔬.*?(?=\n### Sunology)", section.rstrip())

# Homepage: keep Windows + Python cards only.
text = read("docs/index.html")
text = re.sub(r'\s*<a class="card"[^>]*href="test-your-inverter\.html#mac-linux".*?</a>', '', text, flags=re.S)
text = text.replace('One script for Windows, macOS and Linux, with clear terminal commands.', 'Python 3.10+ command-line diagnostic with clear terminal commands.')
write("docs/index.html", text)

# Public diagnostic page: Windows app + generic Python only.
text = read("docs/test-your-inverter.html")
repls = {
'Test whether your TSUN microinverter works locally with Home Assistant using the same TSUN Local Diagnostic interface on Windows, macOS, Linux or directly with Python.':'Test whether your TSUN microinverter works locally with Home Assistant using the Windows TSUN Local Diagnostic app or Python.',
'Use the read-only TSUN Local Diagnostic on Windows, macOS, Linux or directly with Python and optionally upload an anonymized hardware report after explicit consent.':'Use the read-only TSUN Local Diagnostic on Windows or Python and optionally upload an anonymized hardware report after explicit consent.',
'Read-only TSUN Local Diagnostic for Windows, macOS, Linux and Python.':'Read-only TSUN Local Diagnostic for Windows and Python.',
'Run tsun_dump.py with Python 3.10+ or launch the TSUN Local Diagnostic desktop package for Windows, macOS or Linux.':'Run tsun_dump.py with Python 3.10+ or launch the TSUN Local Diagnostic desktop package for Windows.',
'Start with the Windows app, use Python on any platform, or choose the packaged Mac/Linux app.':'Start with the Windows app or use the Python diagnostic.',
'Windows · Python 3.10+ · macOS &amp; Linux · Strictly read-only':'Windows · Python 3.10+ · Strictly read-only',
'Prefer the terminal? Download <code>tsun_dump.py</code> and run it with Python 3.10+ on Windows, macOS or Linux.':'Prefer the terminal? Download <code>tsun_dump.py</code> and run it with Python 3.10+.',
'Use Windows, Python, Mac or Linux. Discovery and evidence capture remain read-only.':'Use the Windows app or Python. Discovery and evidence capture remain read-only.',
}
for a, b in repls.items(): text = text.replace(a, b)
text = text.replace('python3 tsun_dump.py', 'python tsun_dump.py')
text = re.sub(r'\s*<section id="mac-linux">.*?</section>', '', text, count=1, flags=re.S)
text = re.sub(r'\s*\.mac-warning\{.*?\}\s*\.mac-warning strong\{.*?\}\s*\.mac-warning p\{.*?\}\s*\.mac-warning ol\{.*?\}', '', text, count=1, flags=re.S)
# Replace the first two-card Python command row with a single generic command card.
text = re.sub(r'<div class="command-grid">\s*<div class="command-card"><strong>Windows</strong>.*?</div>\s*<div class="command-card"><strong>macOS / Linux</strong>.*?</div>\s*</div>', '<div class="command-grid"><div class="command-card"><strong>Python 3.10+</strong><pre><code>python tsun_dump.py --full</code></pre></div></div>', text, count=1, flags=re.S)
text = text.replace('<p>On Windows, replace <code>python3</code> with <code>py</code> in the commands above.</p>', '')
write("docs/test-your-inverter.html", text)

# Tools README: public instructions are Windows-only, while Python remains generic.
replace_section("tools/README.md", r"## Desktop diagnostic — Windows, macOS and Linux\n.*?(?=\n## Hardware validation dump)", f'''## Desktop diagnostic — Windows

For users who prefer a guided interface, TSUN Local provides the Windows desktop diagnostic. It uses the same privacy-safe, **strictly read-only** `tsun_dump.py` engine.

| Platform | Download | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [checksum]({WIN}.sha256) |

The historical Windows URL remains unchanged so links in older posts continue to work.

### Python / command-line version

[`tsun_dump.py`]({DUMP}) requires Python 3.10+:

```text
python tsun_dump.py --full
```
'''.rstrip())

# Hardware dump guide: Windows desktop route + generic Python route.
replace_section("docs/HARDWARE_DUMP.md", r"## ⬇️ Choose the easiest diagnostic\n.*?(?=\n### Firmware-resilient logger web capture)", f'''## ⬇️ Choose the easiest diagnostic

### Desktop application — Windows (recommended)

| Platform | Download | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe]({WIN}) | [SHA-256]({WIN}.sha256) |

The Windows application uses the same privacy-safe, **strictly read-only** `tsun_dump.py` hardware engine. Direct report upload is a separate HTTPS action performed only after explicit consent.

### Python / command-line alternative

**[Download `tsun_dump.py`]({DUMP})** — Python 3.10+.

```text
python tsun_dump.py --full
```

The standard flow remains: disable the affected TSUN Local entry, run the capture, review the result, upload only after explicit consent, then re-enable TSUN Local.
'''.rstrip())

# Canonical desktop validation protocol: keep the stable path but describe Windows only.
text = read("docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md")
text = text.replace('TSUN Local Diagnostic — cross-platform validation protocol', 'TSUN Local Diagnostic — Windows validation protocol')
text = re.sub(r'## Scope\n.*?(?=\n## Stable download channel)', '''## Scope

The guided desktop diagnostic is published for Windows x86_64 as `TSUN-Local-Diagnostic.exe`.

The user flow remains:

1. **Disable TSUN Local** for the logger being tested.
2. **Run the diagnostic**.
3. **Direct report upload** — recommended, explicit consent required.
4. **Manual e-mail report** — optional fallback only.

The Python `tsun_dump.py` tool remains available for advanced/terminal use and keeps the same read-only behavior.
'''.rstrip(), text, count=1, flags=re.S)
text = re.sub(r'\n### macOS\n.*?(?=\n### Linux|\n## Regression rule)', '', text, flags=re.S)
text = re.sub(r'\n### Linux\n.*?(?=\n## Regression rule)', '', text, flags=re.S)
text = '\n'.join(line for line in text.splitlines() if 'macOS' not in line and 'Linux' not in line)
text = text.replace('All desktop packages and the Python dumper', 'The Windows desktop package and the Python dumper')
text = text.replace('Run these checks on each desktop platform when practical:', 'Run these checks on Windows when practical:')
text = text.replace('Explorer / Finder /  desktop file manager', 'Explorer')
write("docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md", text + ('' if text.endswith('\n') else '\n'))

# Tests: assert the removed public route stays gone.
text = read("tests/test_metadata.py")
text = text.replace("        self.assertIn('Mac &amp; Linux diagnostic →', index)\n", "        self.assertNotIn('Mac &amp; Linux diagnostic →', index)\n        self.assertNotIn('test-your-inverter.html#mac-linux', index)\n")
write("tests/test_metadata.py", text)
text = read("tests/test_release_154_web.py")
text = text.replace('        self.assertIn("test-your-inverter.html#mac-linux", text)\n', '        self.assertNotIn("test-your-inverter.html#mac-linux", text)\n')
write("tests/test_release_154_web.py", text)

# Remove obsolete documentation generators/signing notes so they cannot reintroduce the removed public content.
for rel in (
    "docs/MACOS_SIGNING.md",
    "scripts/clarify_macos_diagnostic_docs.py",
    "scripts/publish_macos_first_launch_docs.py",
    "scripts/sync_diagnostic_docs.py",
):
    p = ROOT / rel
    if p.exists(): p.unlink()

# Guardrails on the requested public surfaces.
public = ["README.md", *localized.keys(), "docs/index.html", "docs/test-your-inverter.html", "tools/README.md", "docs/HARDWARE_DUMP.md", "docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md"]
for rel in public:
    t = read(rel)
    for forbidden in ("TSUN-Local-Diagnostic-macOS", "TSUN-Local-Diagnostic-Linux", "#mac-linux", "Mac &amp; Linux diagnostic"):
        if forbidden in t:
            raise RuntimeError(f"{forbidden!r} still present in {rel}")

# Remove temporary files in the same cleanup commit.
for rel in ("scripts/_cleanup_public_diagnostic_docs.py", ".github/workflows/remove-mac-linux-diagnostics.yml"):
    p = ROOT / rel
    if p.exists(): p.unlink()

print("Public diagnostic documentation is Windows-only; Python remains generic.")
