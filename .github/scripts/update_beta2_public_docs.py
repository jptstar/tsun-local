from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(path: str, old: str, new: str) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(
            f"{path}: expected exactly one match, found {count}: {old!r}"
        )
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# README beta banner in all eight documentation languages.
beta_banners = {
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
for path, banner in beta_banners.items():
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    if "1.6.0-beta.2" in text.split(marker, 1)[-1][:700]:
        continue
    if text.count(marker) != 1:
        raise SystemExit(f"{path}: expected one stable version marker")
    p.write_text(text.replace(marker, marker + "\n" + banner, 1), encoding="utf-8")


# Project website: advertise beta2 while keeping 1.5.4 clearly stable.
replace_once(
    "docs/index.html",
    'content="Monitor TSUN microinverters locally in Home Assistant with TSUN Local 1.5.4. Validated on TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2; no cloud or proxy."',
    'content="Monitor TSUN microinverters locally in Home Assistant with TSUN Local. Stable 1.5.4; beta 1.6.0-beta.2 adds adaptive polling. Validated on TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2; no cloud or proxy."',
)
replace_once(
    "docs/index.html",
    'content="Automatic local TSUN microinverter monitoring in Home Assistant. Read-only, no cloud, no proxy, with clear-text alarms in 1.5.4."',
    'content="Local TSUN microinverter monitoring in Home Assistant. Stable 1.5.4; beta 1.6.0-beta.2 adds adaptive polling. Read-only, no cloud, no proxy."',
)
old_preview = '''      <aside class="preview-card" aria-label="TSUN Local 1.5.4 highlights">
        <span class="preview-kicker">NEW IN 1.5.4</span>
        <h3>More 02B0 diagnostics</h3>
        <div class="preview-primary">
          <strong>Temperature, inverter firmware and additional read-only diagnostics</strong>
          <span>02B0 devices now expose nine additional operating and configuration diagnostics without adding any inverter write operation.</span>
        </div>
        <div class="preview-stats">
          <div class="preview-stat"><strong>9</strong><span>new 02B0 diagnostic entities</span></div>
          <div class="preview-stat"><strong>0</strong><span>new write operations<br>read-only by design</span></div>
        </div>
        <div class="preview-note">Product compliance type remains raw until its country/grid-profile meaning is independently validated.</div>
      </aside>'''
new_preview = '''      <aside class="preview-card" aria-label="TSUN Local 1.6.0-beta.2 highlights">
        <span class="preview-kicker">BETA 1.6.0-beta.2</span>
        <h3>Adaptive polling</h3>
        <div class="preview-primary">
          <strong>Automatic communication pacing for unstable and offline micro-inverters</strong>
          <span>Enabled by default in beta2. TSUN Local progressively adjusts polling after communication failures and returns toward the normal interval after successful reads.</span>
        </div>
        <div class="preview-stats">
          <div class="preview-stat"><strong>20 s</strong><span>normal interval</span></div>
          <div class="preview-stat"><strong>300 s</strong><span>offline / night interval</span></div>
        </div>
        <div class="preview-note">Default retry interval: 30 s · Offline after 3 consecutive protocol failures · Available through HACS beta versions.</div>
      </aside>'''
replace_once("docs/index.html", old_preview, new_preview)
replace_once(
    "docs/index.html",
    '<div class="card"><strong>📡 Communication</strong><span class="muted">Online state, last successful communication, duration and consecutive failures.</span></div>',
    '<div class="card"><strong>📡 Communication</strong><span class="muted">Online state plus concise adaptive-polling diagnostics: state, last response, failures and current interval.</span></div>',
)
replace_once(
    "docs/index.html",
    '<div class="install-note">Automatic discovery · Local · Read-only · No cloud · No proxy</div>',
    '<div class="install-note">Automatic discovery · Local · Read-only · No cloud · No proxy</div>\n    <div class="install-note">Testing 1.6.0-beta.2: HACS → TSUN Local → Redownload → show beta versions → 1.6.0-beta.2.</div>',
)


# Website entity reference: add a beta2 section without rewriting stable tables.
replace_once(
    "docs/entities.html",
    '.badge{display:inline-block;padding:5px 9px;border-radius:999px;color:#0d684d;background:var(--green-soft);font-size:12px;font-weight:850}.stable{color:#0d684d;background:var(--green-soft)}',
    '.badge{display:inline-block;padding:5px 9px;border-radius:999px;color:#0d684d;background:var(--green-soft);font-size:12px;font-weight:850}.stable{color:#0d684d;background:var(--green-soft)}.beta{color:var(--amber);background:var(--amber-soft)}',
)
replace_once(
    "docs/entities.html",
    'content="Home Assistant entity reference for stable TSUN Local 1.5.4: PV and AC telemetry, communication diagnostics, readable alarms, TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2."',
    'content="Home Assistant entity reference for TSUN Local: stable 1.5.4 plus 1.6.0-beta.2 adaptive-polling diagnostics, PV and AC telemetry, readable alarms, TSOL-MP3000, TSOL-MX500, TSOL-MS800 and Sunology PLAY2."',
)
common_section = '''  <section><h2>Common everyday entities</h2><div class="grid"><div class="card"><strong>PV production</strong><code>pvN_voltage</code><br><code>pvN_current</code><br><code>pvN_power</code><br><code>pvN_energy_today</code><br><code>pvN_energy_total</code></div><div class="card"><strong>AC production</strong><code>ac_voltage</code><br><code>ac_current</code><br><code>ac_frequency</code><br><code>ac_power</code><br><code>ac_energy_today</code><br><code>ac_energy_total</code></div><div class="card"><strong>Communication</strong><code>communication_online</code><br><code>communication_last_success</code><br><code>communication_duration</code><br><code>communication_blocks</code><br><code>communication_failures</code></div></div><p class="intro" style="margin-top:18px">PV entities are dynamic: only inputs actually detected by TSUN Local are created.</p></section>'''
beta_section = common_section + '''

  <section><span class="badge beta">BETA 1.6.0-beta.2</span><h2>Adaptive polling communication diagnostics</h2><p class="intro">Beta2 enables adaptive polling by default and keeps the everyday communication view compact.</p><table><thead><tr><th>Entity key</th><th>Home Assistant name</th><th>Default</th></tr></thead><tbody><tr><td><code>adaptive_polling_state</code></td><td>Com. — State</td><td>✅</td></tr><tr><td><code>communication_last_success</code></td><td>Com. — Last response</td><td>✅</td></tr><tr><td><code>communication_failures</code></td><td>Com. — Failures</td><td>✅</td></tr><tr><td><code>adaptive_polling_interval</code></td><td>Com. — Interval</td><td>✅</td></tr><tr><td><code>communication_duration</code></td><td>Com. — Duration</td><td>🛡️</td></tr><tr><td><code>communication_blocks</code></td><td>Com. — Blocks</td><td>🛡️</td></tr><tr><td><code>communication_successes_consecutive</code></td><td>Com. — Successes</td><td>🛡️</td></tr><tr><td><code>adaptive_polling_reason</code></td><td>Com. — Reason</td><td>🛡️</td></tr><tr><td><code>adaptive_backoff_events</code></td><td>Com. — Backoff</td><td>🛡️</td></tr></tbody></table><div class="note">Beta2 defaults: 20 s normal · 30 s after an error · 300 s offline/night · offline after 3 consecutive protocol failures. If the logger HTTP page cannot provide a current Wi-Fi value during the periodic refresh, the Wi-Fi diagnostic reports 0% instead of keeping an older percentage visible.</div></section>'''
replace_once("docs/entities.html", common_section, beta_section)


# Markdown entity reference.
entities = ROOT / "docs/ENTITIES.md"
entities_text = entities.read_text(encoding="utf-8")
legend_end = "| 🔬 | Field-validation candidate; live read confirmed but semantic validation still pending |\n\n---\n"
beta_md = """| 🔬 | Field-validation candidate; live read confirmed but semantic validation still pending |

---

## 1.6.0-beta.2 — adaptive polling diagnostics

Beta2 enables **adaptive polling by default** for entries without an explicit stored choice. Default timing is **20 s normal · 30 s after an error · 300 s offline/night**, with offline state after **3 consecutive protocol failures**.

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

The logger Wi-Fi value remains diagnostic only. During the periodic HTTP refresh, an unavailable current Wi-Fi reading is exposed as **0%** instead of leaving a previous percentage visible. Online/offline state and adaptive pacing remain based on protocol communication results.

---
"""
if "## 1.6.0-beta.2 — adaptive polling diagnostics" not in entities_text:
    if entities_text.count(legend_end) != 1:
        raise SystemExit("docs/ENTITIES.md: legend insertion point not unique")
    entities.write_text(entities_text.replace(legend_end, beta_md, 1), encoding="utf-8")


# Mirror beta2 notes to main so the existing release-notes workflow can sync the public release.
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

A periodic logger HTTP refresh that cannot obtain a current Wi-Fi signal reports **0%** instead of leaving an older percentage visible. This prevents a stale RSSI value from looking current after the logger web interface becomes unreachable.

## Clearer Home Assistant UI

The options page now uses shorter polling terminology. Communication diagnostics are grouped with short `Com. —` names. The four primary diagnostics remain enabled by default: state, last response, failures and current interval. Duration, blocks, successes, reason and backoff remain available as advanced diagnostics but are disabled by default.

Country/profile diagnostics use one consistent visible label across protocol families while protocol-specific internal keys remain unchanged.

## Field-test checkpoint

Nighttime field captures on one 1511 TITAN device and one 02B0 GEN3 device showed the intended transition from normal polling to the configured protocol-failure threshold and then to the **300 s offline cadence**. Beta2 is intended to verify the equally important morning recovery on additional real hardware without manually reloading TSUN Local.

The beta release pipeline reran unit tests, HACS validation and Hassfest before the release tag was created.

## Scope

This beta does **not** learn a permanent per-device optimum polling interval. After successful recovery it still progressively targets the configured normal interval. A future learning/stability layer can be evaluated from beta2 field curves if repeated oscillation between normal and degraded intervals is observed.
""",
    encoding="utf-8",
)
