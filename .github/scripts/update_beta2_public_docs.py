from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match for {old!r}, got {text.count(old)}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Keep 1.5.4 clearly identified as stable, while advertising beta2 for testing.
banners = {
    "README.md": '<p align="center"><strong>Beta 1.6.0-beta.2 available for testing.</strong><br>Adaptive polling is enabled by default: 20 s normal · 30 s after an error · 300 s offline/night. In HACS, show beta versions and download <strong>1.6.0-beta.2</strong>.</p>',
    "docs/README_FR.md": '<p align="center"><strong>Bêta 1.6.0-beta.2 disponible pour test.</strong><br>La relève adaptative est activée par défaut : 20 s normal · 30 s après erreur · 300 s hors ligne/nuit. Dans HACS, affichez les versions bêta puis téléchargez <strong>1.6.0-beta.2</strong>.</p>',
    "docs/README_DE.md": '<p align="center"><strong>Beta 1.6.0-beta.2 zum Testen verfügbar.</strong><br>Der adaptive Abruf ist standardmäßig aktiviert: 20 s normal · 30 s nach einem Fehler · 300 s offline/Nacht. In HACS Beta-Versionen anzeigen und <strong>1.6.0-beta.2</strong> herunterladen.</p>',
    "docs/README_ES.md": '<p align="center"><strong>Beta 1.6.0-beta.2 disponible para pruebas.</strong><br>La lectura adaptativa está activada de forma predeterminada: 20 s normal · 30 s tras un error · 300 s sin conexión/noche. En HACS, muestre las versiones beta y descargue <strong>1.6.0-beta.2</strong>.</p>',
    "docs/README_IT.md": '<p align="center"><strong>Beta 1.6.0-beta.2 disponibile per i test.</strong><br>La lettura adattiva è attiva per impostazione predefinita: 20 s normale · 30 s dopo un errore · 300 s offline/notte. In HACS, mostra le versioni beta e scarica <strong>1.6.0-beta.2</strong>.</p>',
    "docs/README_NL.md": '<p align="center"><strong>Beta 1.6.0-beta.2 beschikbaar om te testen.</strong><br>Adaptief uitlezen staat standaard aan: 20 s normaal · 30 s na een fout · 300 s offline/nacht. Toon in HACS de bètaversies en download <strong>1.6.0-beta.2</strong>.</p>',
    "docs/README_PL.md": '<p align="center"><strong>Beta 1.6.0-beta.2 jest dostępna do testów.</strong><br>Odczyt adaptacyjny jest domyślnie włączony: 20 s normalnie · 30 s po błędzie · 300 s offline/noc. W HACS pokaż wersje beta i pobierz <strong>1.6.0-beta.2</strong>.</p>',
    "docs/README_ZH.md": '<p align="center"><strong>1.6.0-beta.2 测试版现已可用。</strong><br>自适应采集默认启用：正常 20 秒 · 出错后 30 秒 · 离线/夜间 300 秒。在 HACS 中显示测试版并下载 <strong>1.6.0-beta.2</strong>。</p>',
}
marker = '<br><strong>1.5.4</strong></p>'
for path, banner in banners.items():
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if banner in text:
        continue
    if text.count(marker) != 1:
        raise SystemExit(f"{path}: stable version marker not unique")
    p.write_text(text.replace(marker, marker + "\n" + banner, 1), encoding="utf-8")


# Homepage: retain all stable 1.5.4 identity/SEO guarantees, add a separate beta2 card.
replace_once(
    "docs/index.html",
    'content="Monitor TSUN microinverters locally in Home Assistant with TSUN Local 1.5.4. Validated on TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2; no cloud or proxy."',
    'content="Monitor TSUN microinverters locally in Home Assistant with TSUN Local 1.5.4. Beta 1.6.0-beta.2 adds adaptive polling. Validated on TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2; no cloud or proxy."',
)
replace_once(
    "docs/index.html",
    'content="Automatic local TSUN microinverter monitoring in Home Assistant. Read-only, no cloud, no proxy, with clear-text alarms in 1.5.4."',
    'content="Automatic local TSUN microinverter monitoring in Home Assistant. Stable 1.5.4 keeps clear-text alarms; beta 1.6.0-beta.2 adds adaptive polling. Read-only, no cloud, no proxy."',
)
beta_home = '''<main class="wrap">
  <section id="beta2">
    <span class="section-badge beta">BETA 1.6.0-beta.2</span>
    <h2>Adaptive polling for unstable and offline communication</h2>
    <p class="intro">Beta2 enables adaptive polling by default. TSUN Local starts at 20 s, retries after an error at 30 s, and uses 300 s when the configured failure threshold marks the micro-inverter offline. Successful reads progressively return polling toward the normal interval.</p>
    <div class="grid">
      <div class="card"><strong>20 s</strong><span class="muted">Normal interval</span></div>
      <div class="card"><strong>30 s</strong><span class="muted">Interval after an error</span></div>
      <div class="card"><strong>300 s</strong><span class="muted">Offline / night interval</span></div>
    </div>
    <div class="install-note">Test it in HACS: TSUN Local → Redownload → show beta versions → 1.6.0-beta.2.</div>
  </section>'''
replace_once("docs/index.html", '<main class="wrap">', beta_home)
replace_once(
    "docs/index.html",
    '<div class="card"><strong>📡 Communication</strong><span class="muted">Online state, last successful communication, duration and consecutive failures.</span></div>',
    '<div class="card"><strong>📡 Communication</strong><span class="muted">Online state plus concise adaptive-polling diagnostics: state, last response, failures and current interval.</span></div>',
)


# Visual entity reference: add beta2 communication diagnostics but keep stable sections intact.
replace_once(
    "docs/entities.html",
    '.badge{display:inline-block;padding:5px 9px;border-radius:999px;color:#0d684d;background:var(--green-soft);font-size:12px;font-weight:850}.stable{color:#0d684d;background:var(--green-soft)}',
    '.badge{display:inline-block;padding:5px 9px;border-radius:999px;color:#0d684d;background:var(--green-soft);font-size:12px;font-weight:850}.stable{color:#0d684d;background:var(--green-soft)}.beta{color:var(--amber);background:var(--amber-soft)}',
)
replace_once(
    "docs/entities.html",
    'content="Home Assistant entity reference for stable TSUN Local 1.5.4: PV and AC telemetry, communication diagnostics, readable alarms, TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2."',
    'content="Home Assistant entity reference for TSUN Local: stable 1.5.4 plus beta 1.6.0-beta.2 adaptive-polling diagnostics, PV and AC telemetry, readable alarms, TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2."',
)
anchor = '  <section><span class="badge stable">1.5.4 STABLE</span><h2>Readable alarm entities</h2>'
beta_entities = '''  <section><span class="badge beta">BETA 1.6.0-beta.2</span><h2>Adaptive polling communication diagnostics</h2><p class="intro">Beta2 enables adaptive polling by default and keeps the everyday communication view compact.</p><table><thead><tr><th>Entity key</th><th>Home Assistant name</th><th>Default</th></tr></thead><tbody><tr><td><code>adaptive_polling_state</code></td><td>Com. — State</td><td>✅</td></tr><tr><td><code>communication_last_success</code></td><td>Com. — Last response</td><td>✅</td></tr><tr><td><code>communication_failures</code></td><td>Com. — Failures</td><td>✅</td></tr><tr><td><code>adaptive_polling_interval</code></td><td>Com. — Interval</td><td>✅</td></tr><tr><td><code>communication_duration</code></td><td>Com. — Duration</td><td>🛡️</td></tr><tr><td><code>communication_blocks</code></td><td>Com. — Blocks</td><td>🛡️</td></tr><tr><td><code>communication_successes_consecutive</code></td><td>Com. — Successes</td><td>🛡️</td></tr><tr><td><code>adaptive_polling_reason</code></td><td>Com. — Reason</td><td>🛡️</td></tr><tr><td><code>adaptive_backoff_events</code></td><td>Com. — Backoff</td><td>🛡️</td></tr></tbody></table><div class="note">Defaults: 20 s normal · 30 s after error · 300 s offline/night · offline after 3 consecutive protocol failures. If the periodic logger HTTP refresh cannot obtain a current Wi-Fi signal, the Wi-Fi diagnostic reports 0% instead of retaining an older percentage.</div></section>\n\n'''
replace_once("docs/entities.html", anchor, beta_entities + anchor)


# Markdown entity reference.
entities = ROOT / "docs/ENTITIES.md"
text = entities.read_text(encoding="utf-8")
legend = "| 🔬 | Field-validation candidate; live read confirmed but semantic validation still pending |\n\n---\n"
section = """| 🔬 | Field-validation candidate; live read confirmed but semantic validation still pending |

---

## 1.6.0-beta.2 — adaptive polling diagnostics

Beta2 enables **adaptive polling by default** for entries without an explicit stored choice. Defaults are **20 s normal · 30 s after an error · 300 s offline/night**, with offline state after **3 consecutive protocol failures**.

| Entity key | Home Assistant name | Default |
|---|---|:---:|
| `adaptive_polling_state` | Com. — State | ✅ |
| `communication_last_success` | Com. — Last response | ✅ |
| `communication_failures` | Com. — Failures | ✅ |
| `adaptive_polling_interval` | Com. — Interval | ✅ |
| `communication_duration` | Com. — Duration | 🛡️ |
| `communication_blocks` | Com. — Blocks | 🛡️ |
| `communication_successes_consecutive` | Com. — Successes | 🛡️ |
| `adaptive_polling_reason` | Com. — Reason | 🛡️ |
| `adaptive_backoff_events` | Com. — Backoff | 🛡️ |

Logger Wi-Fi remains diagnostic only. If the periodic HTTP refresh cannot obtain a current signal, beta2 exposes **0%** instead of leaving the previous percentage visible. Online/offline state and adaptive pacing remain driven by protocol communication results.

---
"""
if "## 1.6.0-beta.2 — adaptive polling diagnostics" not in text:
    if text.count(legend) != 1:
        raise SystemExit("docs/ENTITIES.md: legend insertion point not unique")
    entities.write_text(text.replace(legend, section, 1), encoding="utf-8")


# Correct public release notes: nighttime transition is validated; morning recovery remains a beta2 test target.
notes = ROOT / "docs/releases/1.6.0-beta.2.md"
notes.write_text(
    """# TSUN Local 1.6.0-beta.2

This second 1.6.0 beta makes adaptive polling the default and simplifies its user-facing controls and diagnostics.

## Adaptive polling defaults

- Adaptive polling is enabled by default for entries that do not already store an explicit user choice. Existing explicit settings remain respected.
- Normal interval: **20 s**.
- Interval after an error: **30 s**.
- Offline / night interval: **300 s**.
- Offline threshold: **3 consecutive protocol failures**.

Adaptive polling remains driven by actual protocol communication results. Logger Wi-Fi RSSI is diagnostic only and does not control online/offline state or polling cadence.

## Logger Wi-Fi diagnostic

A periodic logger HTTP refresh that cannot obtain a current Wi-Fi signal reports **0%** instead of leaving an older percentage visible.

## Clearer Home Assistant UI

The options page uses shorter polling terminology. Communication diagnostics use short `Com. —` names. State, last response, failures and current interval remain enabled by default; duration, blocks, successes, reason and backoff are advanced diagnostics disabled by default.

Country/profile diagnostics use one consistent visible label across protocol families while protocol-specific internal keys remain unchanged.

## Field-test checkpoint

Nighttime field captures on one 1511 TITAN device and one 02B0 GEN3 device showed the intended transition from normal polling to the configured failure threshold and then to the **300 s offline cadence**. Beta2 is intended to verify the equally important morning recovery on additional real hardware without manually reloading TSUN Local.

The beta release pipeline reran unit tests, HACS validation and Hassfest before the release tag was created.

## Scope

This beta does **not** learn a permanent per-device optimum polling interval. After successful recovery it still progressively targets the configured normal interval. A future learning/stability layer can be evaluated from beta2 field curves if repeated oscillation between normal and degraded intervals is observed.
""",
    encoding="utf-8",
)
