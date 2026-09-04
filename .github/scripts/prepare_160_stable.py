from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[2]
version = "1.6.0"

manifest = json.loads((root / "custom_components/tsun_local/manifest.json").read_text(encoding="utf-8"))
if manifest.get("version") != version:
    raise SystemExit(f"Unexpected manifest version: {manifest.get('version')}")

# CHANGELOG: add one concise stable section, preserving all historical releases.
changelog = root / "CHANGELOG.md"
text = changelog.read_text(encoding="utf-8")
if "## [1.6.0] - 2026-09-04" not in text:
    section = """## [1.6.0] - 2026-09-04

### Added

- Add **adaptive polling**, enabled by default for entries without an explicit stored choice.
- Add chartable communication diagnostics for adaptive state, effective polling interval, consecutive successes/failures, adaptation reason and slowdown events.
- Add a per-logger FIFO request queue so one slow or unavailable logger does not block unrelated TSUN devices.

### Changed

- Use default polling limits of **20 s normal**, **30 s after an error** and **300 s offline/night**, with offline state after **3 consecutive protocol failures**.
- Keep an explicitly saved adaptive-polling choice, including an existing explicit disabled setting.
- Report logger Wi-Fi signal as **0%** when the periodic local HTTP refresh cannot obtain a current value instead of retaining a stale percentage.
- Group communication entities under full localized **Communication** labels; the four everyday entities remain enabled by default while duration, blocks, successes, reason and slowdown count remain advanced diagnostics.
- Harmonize the visible country/profile diagnostic wording across protocol families while keeping protocol-specific internal keys stable.

### Fixed

- Bound TCP writer shutdown on 02B0, 1097 and 1511 so a hanging stream close cannot stall integration cleanup.
- Keep adaptive availability based on actual protocol polling failures; logger Wi-Fi remains diagnostic only.
- Mark a micro-inverter online on the first successful protocol poll after an offline period, then recover the polling cadence progressively toward the configured normal interval.

### Validation

- Validate all eight interface languages: English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese.
- Run the complete unit-test suite, HACS repository validation and Home Assistant Hassfest before publication.

"""
    marker = re.search(r"(?m)^## \[", text)
    if not marker:
        raise SystemExit("Could not locate first CHANGELOG release heading")
    text = text[: marker.start()] + section + text[marker.start() :]
    changelog.write_text(text, encoding="utf-8")

# Stable release notes used by the publication workflow.
notes = root / "docs/releases/1.6.0.md"
notes.write_text(
    """# TSUN Local 1.6.0

TSUN Local 1.6.0 promotes the adaptive communication work tested in the 1.6.0 beta series to the stable release.

## Adaptive polling

Adaptive polling is enabled by default for entries that do not already store an explicit user choice. Existing explicit choices remain respected.

Default settings are:

- **20 s** normal interval
- **30 s** after a communication error
- **300 s** offline / night interval
- offline after **3 consecutive protocol failures**

When the failure threshold is reached, TSUN Local marks the micro-inverter offline and uses the configured offline interval. The first successful protocol response marks it online immediately; the polling interval then returns progressively toward the configured normal value.

The adaptive algorithm reacts to protocol communication results. Logger Wi-Fi signal is diagnostic only and does not independently change availability or polling cadence.

## Communication and logger reliability

- Requests are serialized per logger with a FIFO queue, so an unavailable logger does not block unrelated TSUN devices.
- TCP stream shutdown is bounded on 02B0, 1097 and 1511.
- If the logger HTTP interface cannot provide a current Wi-Fi value during the periodic refresh, the Wi-Fi diagnostic reports **0%** rather than retaining an older percentage.

## Clearer Home Assistant diagnostics

Communication entities use full localized **Communication — ...** names. The primary state, last response, failures and effective interval are enabled by default. Duration, blocks, consecutive successes, adaptation reason and slowdown count remain available as advanced diagnostics disabled by default.

Country/profile diagnostics use consistent visible wording when the underlying meaning is equivalent, while protocol-specific internal entity keys remain unchanged.

## Languages and validation

The 1.6.0 interface is synchronized in **English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese**. The release pipeline runs the complete unit-test suite, HACS validation and Hassfest before publishing the stable tag.

## Scope

TSUN Local remains local and read-only. Version 1.6.0 does not learn a permanent per-device optimum polling interval: after successful recovery, adaptive polling still progressively targets the configured normal interval.
""",
    encoding="utf-8",
)

# README headers and current-release highlights in every published language.
readmes = {
    "README.md": "**New in 1.6.0:** **Adaptive polling** is enabled by default and automatically adjusts the read interval after communication failures: 20 s normal, 30 s after an error and 300 s offline/night.",
    "docs/README_FR.md": "**Nouveau dans la 1.6.0 :** la **relève adaptative** est activée par défaut et ajuste automatiquement la cadence de lecture en cas d’échecs de communication : 20 s en fonctionnement normal, 30 s après erreur et 300 s hors ligne/nuit.",
    "docs/README_DE.md": "**Neu in 1.6.0:** Der **adaptive Abruf** ist standardmäßig aktiviert und passt das Abfrageintervall bei Kommunikationsfehlern automatisch an: 20 s normal, 30 s nach einem Fehler und 300 s offline/Nacht.",
    "docs/README_ES.md": "**Nuevo en 1.6.0:** La **lectura adaptativa** está activada de forma predeterminada y ajusta automáticamente el intervalo ante fallos de comunicación: 20 s normal, 30 s tras un error y 300 s sin conexión/noche.",
    "docs/README_IT.md": "**Novità in 1.6.0:** La **lettura adattiva** è attiva per impostazione predefinita e regola automaticamente l’intervallo in caso di errori di comunicazione: 20 s normale, 30 s dopo un errore e 300 s offline/notte.",
    "docs/README_NL.md": "**Nieuw in 1.6.0:** **Adaptief uitlezen** staat standaard aan en past het uitleesinterval automatisch aan bij communicatiefouten: 20 s normaal, 30 s na een fout en 300 s offline/nacht.",
    "docs/README_PL.md": "**Nowość w 1.6.0:** **Odczyt adaptacyjny** jest domyślnie włączony i automatycznie dostosowuje interwał przy błędach komunikacji: 20 s normalnie, 30 s po błędzie i 300 s offline/noc.",
    "docs/README_ZH.md": "**1.6.0 新增：** **自适应采集**默认启用，并在通信失败时自动调整采集间隔：正常 20 秒、出错后 30 秒、离线/夜间 300 秒。",
}
for filename, highlight in readmes.items():
    path = root / filename
    original = path.read_text(encoding="utf-8")
    lines = [line for line in original.splitlines() if "1.6.0-beta.2" not in line]
    text = "\n".join(lines) + ("\n" if original.endswith("\n") else "")
    text = text.replace("<strong>1.5.4</strong>", "<strong>1.6.0</strong>", 1)
    text, count = re.subn(r"(?m)^\*\*[^\n]*1\.5\.4[^\n]*$", highlight, text, count=1)
    if count != 1:
        raise SystemExit(f"{filename}: could not replace current-release highlight")
    if "1.6.0-beta.2" in text:
        raise SystemExit(f"{filename}: beta2 wording remains")
    path.write_text(text, encoding="utf-8")

# Homepage: promote adaptive polling from beta to stable 1.6.0.
path = root / "docs/index.html"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "Monitor TSUN microinverters locally in Home Assistant with TSUN Local 1.5.4. Beta 1.6.0-beta.2 adds adaptive polling.",
    "Monitor TSUN microinverters locally in Home Assistant with TSUN Local 1.6.0, including adaptive polling.",
)
text = text.replace(
    "Automatic local TSUN microinverter monitoring in Home Assistant. Stable 1.5.4 keeps clear-text alarms; beta 1.6.0-beta.2 adds adaptive polling. Read-only, no cloud, no proxy.",
    "Automatic local TSUN microinverter monitoring in Home Assistant with TSUN Local 1.6.0 adaptive polling. Read-only, no cloud, no proxy.",
)
text = text.replace('"softwareVersion":"1.5.4"', '"softwareVersion":"1.6.0"')
old_preview = re.compile(r'      <aside class="preview-card" aria-label="TSUN Local 1\.5\.4 highlights">.*?      </aside>', re.S)
new_preview = """      <aside class="preview-card" aria-label="TSUN Local 1.6.0 highlights">
        <span class="preview-kicker">NEW IN 1.6.0</span>
        <h3>Adaptive polling</h3>
        <div class="preview-primary">
          <strong>Automatic communication pacing for unstable and offline micro-inverters</strong>
          <span>Enabled by default. TSUN Local reacts to protocol failures, slows polling when communication becomes unavailable and progressively returns toward the normal interval after successful reads.</span>
        </div>
        <div class="preview-stats">
          <div class="preview-stat"><strong>20 s</strong><span>normal interval</span></div>
          <div class="preview-stat"><strong>300 s</strong><span>offline / night interval</span></div>
        </div>
        <div class="preview-note">Default retry interval: 30 s · Offline after 3 consecutive protocol failures · Logger Wi-Fi remains diagnostic only.</div>
      </aside>"""
text, count = old_preview.subn(new_preview, text, count=1)
if count != 1:
    raise SystemExit("docs/index.html: old preview card not found")
text = text.replace('id="beta2"', 'id="adaptive-polling"')
text = text.replace('<span class="section-badge beta">BETA 1.6.0-beta.2</span>', '<span class="section-badge good">NEW IN 1.6.0</span>')
text = text.replace("Beta2 enables adaptive polling by default.", "TSUN Local 1.6.0 enables adaptive polling by default.")
text = text.replace(
    "Test it in HACS: TSUN Local → Redownload → show beta versions → 1.6.0-beta.2.",
    "Install or update TSUN Local 1.6.0 directly from HACS.",
)
text = text.replace("1.6.0-beta.2", "1.6.0")
if "Beta 1.6.0" in text or "beta 1.6.0" in text:
    raise SystemExit("docs/index.html: beta wording remains around 1.6.0")
path.write_text(text, encoding="utf-8")

# Visual entity reference: stable metadata and adaptive-polling section.
path = root / "docs/entities.html"
text = path.read_text(encoding="utf-8")
text = text.replace(
    "Home Assistant entity reference for TSUN Local: stable 1.5.4 plus beta 1.6.0-beta.2 adaptive-polling diagnostics,",
    "Home Assistant entity reference for stable TSUN Local 1.6.0 with adaptive-polling diagnostics,",
)
text = text.replace(
    "PV, AC, communication, diagnostics and readable alarm entities exposed by TSUN Local 1.5.4 stable.",
    "PV, AC, communication, diagnostics and readable alarm entities exposed by TSUN Local 1.6.0 stable.",
)
text = text.replace(
    "Home Assistant entities for TSUN, Sunology PLAY2, 1511, 02B0 and 1097 in TSUN Local 1.5.4.",
    "Home Assistant entities for TSUN, Sunology PLAY2, 1511, 02B0 and 1097 in TSUN Local 1.6.0.",
)
text = text.replace('<span class="badge beta">BETA 1.6.0-beta.2</span>', '<span class="badge stable">1.6.0 STABLE</span>')
text = text.replace("Beta2 enables adaptive polling by default", "TSUN Local 1.6.0 enables adaptive polling by default")
text = text.replace("1.6.0-beta.2", "1.6.0")
path.write_text(text, encoding="utf-8")

# Markdown entity reference: stable wording, preserving 1.5.4 historical diagnostic sections.
path = root / "docs/ENTITIES.md"
text = path.read_text(encoding="utf-8")
text = text.replace("## 1.6.0-beta.2 — adaptive polling diagnostics", "## 1.6.0 — adaptive polling diagnostics")
text = text.replace("Beta2 enables **adaptive polling by default**", "TSUN Local 1.6.0 enables **adaptive polling by default**")
text = text.replace("beta2 exposes **0%**", "TSUN Local 1.6.0 exposes **0%**")
path.write_text(text, encoding="utf-8")

# Current web/readme contract now targets stable 1.6.0.
web_test = root / "tests/test_release_154_web.py"
text = web_test.read_text(encoding="utf-8")
text = text.replace("Release154WebTests", "Release160WebTests")
text = text.replace("NEW IN 1.5.4", "NEW IN 1.6.0")
text = text.replace("test_public_pages_do_not_advertise_beta_154", "test_public_pages_do_not_advertise_beta_160")
text = text.replace('"1.5.4 beta"', '"1.6.0 beta"')
text = text.replace('"1.5.4-beta"', '"1.6.0-beta"')
web_test.write_text(text, encoding="utf-8")

readme_test = root / "tests/test_stable_151_localized_readmes.py"
text = readme_test.read_text(encoding="utf-8")
text = text.replace("1\\.5\\.4", "1\\.6\\.0")
text = text.replace("Stable154LocalizedReadmeTests", "Stable160LocalizedReadmeTests")
readme_test.write_text(text, encoding="utf-8")

# Translation audit: exact structural parity, no abbreviated communication label/backoff wording.
source = json.loads((root / "custom_components/tsun_local/strings.json").read_text(encoding="utf-8"))

def key_paths(value, prefix=""):
    result = set()
    if not isinstance(value, dict):
        return result
    for key, child in value.items():
        path_key = f"{prefix}.{key}" if prefix else key
        result.add(path_key)
        result |= key_paths(child, path_key)
    return result

expected_keys = key_paths(source)
trans_dir = root / "custom_components/tsun_local/translations"
expected_files = {"en.json", "fr.json", "de.json", "es.json", "it.json", "nl.json", "pl.json", "zh-Hans.json"}
actual_files = {p.name for p in trans_dir.glob("*.json")}
if actual_files != expected_files:
    raise SystemExit(f"Translation files mismatch: {actual_files}")
required_sensor_keys = {
    "communication_last_success",
    "communication_duration",
    "communication_blocks",
    "communication_failures",
    "communication_successes_consecutive",
    "adaptive_polling_interval",
    "adaptive_backoff_events",
    "adaptive_polling_state",
    "adaptive_polling_reason",
}
for translation in sorted(trans_dir.glob("*.json")):
    data = json.loads(translation.read_text(encoding="utf-8"))
    if key_paths(data) != expected_keys:
        raise SystemExit(f"{translation.name}: translation key structure differs from strings.json")
    sensors = data["entity"]["sensor"]
    if not required_sensor_keys <= set(sensors):
        raise SystemExit(f"{translation.name}: missing communication sensors")
    content = translation.read_text(encoding="utf-8")
    if "Com. —" in content or "Backoff" in content:
        raise SystemExit(f"{translation.name}: obsolete communication wording remains")

# Stable publication must not advertise beta2 in current public surfaces.
public_surfaces = [
    root / "README.md",
    *(root / "docs").glob("README_*.md"),
    root / "docs/index.html",
    root / "docs/entities.html",
    root / "docs/ENTITIES.md",
]
for public in public_surfaces:
    if "1.6.0-beta.2" in public.read_text(encoding="utf-8"):
        raise SystemExit(f"{public}: beta2 reference remains in current public documentation")
