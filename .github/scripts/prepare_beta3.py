#!/usr/bin/env python3
from pathlib import Path
import json
import struct

VERSION = "1.5.1-beta.3"


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def must_replace(text: str, old: str, new: str, path: str) -> str:
    if old not in text:
        raise SystemExit(f"Missing expected text in {path}: {old!r}")
    return text.replace(old, new)


if not Path("docs/.prepare-beta3-run").is_file():
    raise SystemExit("Missing beta3 preparation marker")

# Version metadata.
manifest_path = Path("custom_components/tsun_local/manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = VERSION
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

# Root README / HACS presentation.
p = "README.md"
text = read(p).replace("1.5.1-beta.2", VERSION)
beta_row = "| 🚨 | **224 alarm positions preserved** with the same compact Home Assistant interface |"
if "Dedicated Active alarm names" not in text:
    text = must_replace(
        text,
        beta_row,
        "| 🚨 | **Dedicated Active alarm names** sensor exposes localized alarm text directly in Home Assistant |\n"
        "| 📐 | **Overfrequency reduction coefficient corrected** — `0x07EF` raw `4000` → `40.00 %/Hz` (`×0.01`) |\n"
        "| 🌐 | Technical entity IDs stay stable in English; display names and alarm text follow the Home Assistant language |\n"
        + beta_row,
        p,
    )
write(p, text)

# Localized README version labels.
for rp in Path("docs").glob("README_*.md"):
    t = rp.read_text(encoding="utf-8")
    t = t.replace("1.5.1-beta.2", VERSION)
    rp.write_text(t, encoding="utf-8")

# Technical entity reference.
p = "docs/ENTITIES.md"
text = read(p).replace("1.5.1-beta.1", VERSION).replace("1.5.1-beta.2", VERSION)
write(p, text)

# Website home page, preserving design.
p = "docs/index.html"
text = read(p).replace("1.5.1-beta.2", VERSION)
text = text.replace("🧪 NEW IN 1.5.1 BETA 1", "🧪 NEW IN 1.5.1 BETA 3")
text = text.replace("<strong>55</strong><span>enabled by default</span>", "<strong>56</strong><span>enabled by default</span>")
text = text.replace("<strong>50</strong><span>advanced diagnostics</span>", "<strong>49</strong><span>advanced diagnostics</span>")
text = text.replace(
    "The 1.5.0 presentation and alarm architecture stay intact. Beta 1 adds read-only MP3000/TITAN evidence and fixes logger RSSI traversal.",
    "The 1.5.0 presentation and alarm architecture stay intact. Beta 3 consolidates the MP3000 diagnostics, localized alarm-name entity and logger RSSI fixes.",
)
text = text.replace("Active names and local codes without a wall of permanent entities.", "Localized active alarm names without a wall of permanent entities.")
old_beta_grid = '''      <div class="grid">\n        <div class="card"><strong>📶 Wi-Fi RSSI fallback fixed</strong><span class="muted">A valid index page without RSSI no longer stops the search. TSUN Local continues until `/status.html` exposes `cover_sta_rssi`; a live post-fix dump read 30%.</span></div>\n        <div class="card"><strong>🛡️ 10 A1/21 diagnostics</strong><span class="muted">Ten additional MP3000 field-validation sensors are available as advanced entities and remain disabled by default.</span></div>\n      </div>'''
new_beta_grid = '''      <div class="grid">\n        <div class="card"><strong>📶 Wi-Fi RSSI fallback fixed</strong><span class="muted">A valid index page without RSSI no longer stops the search. TSUN Local continues until `/status.html` exposes `cover_sta_rssi`.</span></div>\n        <div class="card"><strong>🛡️ 10 A1/21 diagnostics</strong><span class="muted">Ten additional MP3000 field-validation sensors are available as advanced entities and remain disabled by default.</span></div>\n        <div class="card"><strong>🚨 Active alarm names</strong><span class="muted">A dedicated sensor exposes localized active alarm text directly in Home Assistant. Internal Axxx identifiers stay diagnostic-only.</span></div>\n        <div class="card"><strong>📐 Corrected coefficient</strong><span class="muted"><code>0x07EF</code> raw 4000 is decoded with ×0.01 as <strong>40.00 %/Hz</strong>.</span></div>\n      </div>'''
text = must_replace(text, old_beta_grid, new_beta_grid, p)
text = text.replace("Unidentified inverter alarm (A030)", "Unidentified inverter alarm")
text = text.replace("unique local codes", "stable internal positions")
text = text.replace("<li>Inverter alarm and active alarm count</li>", "<li>Inverter alarm, active alarm count and localized active alarm names</li>")
text = text.replace("1511 country/profile raw candidate and power-level candidate", "1511 country/profile raw candidate")
write(p, text)

# Visual entity page.
p = "docs/entities.html"
text = read(p).replace("1.5.1-beta.1", VERSION).replace("1.5.1-beta.2", VERSION)
text = text.replace("<strong>55</strong><span>enabled by default</span>", "<strong>56</strong><span>enabled by default</span>")
text = text.replace("<strong>50</strong><span>advanced diagnostics</span>", "<strong>49</strong><span>advanced diagnostics</span>")
text = text.replace(
    "<tr><td>Power and capacity diagnostics</td><td>3</td><td>Rated power, designed power and candidate power level</td></tr>",
    "<tr><td>Power and capacity diagnostics</td><td>2</td><td>Rated power and maximum designed power</td></tr>",
)
text = text.replace(
    "<tr><td>Alarm interface</td><td>16</td><td>Alarm state, active count and 14 complete raw words</td></tr>",
    "<tr><td>Alarm interface</td><td>17</td><td>Alarm state, active count, active alarm names and 14 complete raw words</td></tr>",
)
text = text.replace("55 enabled · 50 advanced", "56 enabled · 49 advanced")
text = text.replace("Inverter alarm · active count · localized names · stable local codes.", "Inverter alarm · active count · dedicated localized alarm names.")
text = text.replace("22 core grid protections · 10 field-validation values · temperatures · candidate power level · raw country/profile candidate.", "22 core grid protections · 10 field-validation values · temperatures · raw country/profile candidate.")
text = text.replace("active positions are decoded inside two everyday entities", "active positions are decoded through three everyday entities")
old_alarm_groups = '''        <div class="group"><strong>🚨 Inverter alarm</strong><span class="muted">A problem binary sensor that turns on when an alarm position is active. Its attributes list active localized names and stable local codes.</span></div>\n        <div class="group"><strong>🔢 Active alarms</strong><span class="muted">Counts every active position, including positions whose exact physical meaning is still awaiting validation.</span></div>\n        <div class="group"><strong>🧰 Fourteen raw words</strong><span class="muted">Four inverter words, four secondary words and six PV words. They are disabled by default.</span></div>'''
new_alarm_groups = '''        <div class="group"><strong>🚨 Inverter alarm</strong><span class="muted">A problem binary sensor that turns on when an alarm position is active.</span></div>\n        <div class="group"><strong>🔢 Active alarms</strong><span class="muted">Counts every active position, including positions whose exact physical meaning is still awaiting validation.</span></div>\n        <div class="group"><strong>📝 Active alarm names</strong><span class="muted">Publishes localized alarm text directly. Internal Axxx identifiers remain diagnostic-only.</span></div>\n        <div class="group"><strong>🧰 Fourteen raw words</strong><span class="muted">Four inverter words, four secondary words and six PV words. They are disabled by default.</span></div>'''
text = must_replace(text, old_alarm_groups, new_alarm_groups, p)
text = text.replace(
    "<tr><td><code>grid_overfrequency_reduction_coefficient</code></td><td><code>0x07EF</code></td><td>4000 raw</td></tr>",
    "<tr><td><code>grid_overfrequency_reduction_coefficient</code></td><td><code>0x07EF</code></td><td>4000 × 0.01 = 40.00 %/Hz</td></tr>",
)
write(p, text)

# Research backlog: explicitly kept outside beta3 semantic entities.
write("docs/PENDING_1.5.1.md", '''# TSUN Local 1.5.1 research backlog\n\nThese MP3000/1511 correlations are intentionally **kept out of 1.5.1-beta.3 semantic Home Assistant entities** until independently validated.\n\n## Very strong\n\n- `0x07F1` → Reactive mode candidate, live raw `0x0066`.\n- `0x07F2` → GFCI enable candidate, live raw `1000`.\n- `0x07F9` → Calibration K3 candidate, live raw `1003`.\n- `0x080D` → Anti-current / anti-reflux delay candidate, live raw `10`, profile value `10 s`.\n\n## Strong but order-indeterminate\n\n- `0x07F7` / `0x07F8` → Calibration K1 / K2 candidate pair, both live raw `1024`; individual order is not assigned.\n\n## Very promising cluster\n\n- `0x080B`–`0x080E` → anti-reflux / zero-export configuration cluster. Individual semantic assignments remain pending.\n\n## Still too ambiguous\n\n- `0x07ED` / `0x0809` → reduction-signal candidates.\n- `0x0BD2` → isolation candidate around `60 MΩ`; Rx/Ry assignment is not distinguishable from the current profile.\n\nNo write command is implemented or required for this research backlog.\n''')

# Cumulative release notes: 1.5.0 + beta1 + beta2 + beta3.
write(f"docs/releases/{VERSION}.md", '''# TSUN Local 1.5.1-beta.3\n\nTSUN Local 1.5.1-beta.3 consolidates the complete MP3000 alarm interface introduced in 1.5.0 with the fixes and diagnostics developed through beta1, beta2 and beta3. The integration remains fully local and read-only.\n\n## From 1.5.0 — complete MP3000 alarm interface\n\n- All **224 MP3000 alarm positions** remain covered.\n- **12 functional mappings** are hardware-validated: PV input undervoltage and PV DSP fault for PV1 through PV6.\n- The remaining **212 positions** stay active with neutral wording until their exact physical meaning is validated.\n- The fourteen complete raw alarm words remain available as advanced diagnostics, disabled by default.\n- Alarm presentation is localized in English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese.\n\n## From 1.5.1-beta.1 — MP3000 diagnostics and logger Wi-Fi\n\n- Fix logger Wi-Fi RSSI traversal so a valid page without RSSI no longer prevents reading `cover_sta_rssi` from `/status.html`.\n- Add ten read-only MP3000/TITAN A1/21 field-validation diagnostics, disabled by default.\n- Keep the raw 1511 country/profile candidate available as an advanced diagnostic.\n- Preserve the complete 1.5.0 alarm architecture without creating 224 permanent Home Assistant entities.\n\n## From 1.5.1-beta.2 — localization cleanup\n\n- Remove the unvalidated MP3000/1511 `output_coefficient_candidate` / Power level candidate entity.\n- Keep technical entity IDs and unique IDs stable in English.\n- Verify translated display names for the new MP3000 diagnostics in all eight supported languages.\n- Add regression coverage for translation keys and the complete alarm catalogue.\n- Clean the obsolete beta-only candidate from the Home Assistant entity registry on upgrade.\n\n## New in 1.5.1-beta.3\n\n- Add a dedicated **Active alarm names** sensor (`active_alarm_names`) so localized alarm text is directly visible and usable in Home Assistant.\n- Keep stable `A001`–`A224` identifiers internal/diagnostic; unknown user-facing alarm text no longer exposes those codes.\n- Correct MP3000 `0x07EF`: raw `4000` is decoded with candidate factor `×0.01` and exposed as **40.00 %/Hz**.\n- Refresh README, website and entity pages: up to **105 MP3000 entities** with six PV inputs, **56 enabled by default** and **49 advanced/disabled by default**.\n- Verify HACS metadata and Home Assistant 2026.3+ local `brand/icon*.png` and `brand/logo*.png` assets.\n- Keep the latest reactive-mode, GFCI, calibration and anti-reflux correlations in the research backlog only; beta3 does not promote them to semantic entities.\n\n## Compatibility\n\n- **1511 / TITAN:** validated on TSOL-MP3000.\n- **02B0 / GEN3 / GEN3 PLUS:** validated on TSOL-MX500.\n- **1097 / GEN3 / GEN3 PLUS:** experimental.\n- Home Assistant **2026.3.0 or later**.\n\n## Safety\n\n- All inverter data access remains local and read-only.\n- Logger metadata uses local HTTP GET only.\n- No inverter configuration, protection-setting, country/profile or control write is added.\n\n## Validation\n\nThe beta publication workflow runs the complete unit-test suite, HACS validation and Home Assistant hassfest before creating the immutable prerelease tag.\n''')

# Changelog beta3 section.
p = "CHANGELOG.md"
text = read(p)
if f"## [{VERSION}]" not in text:
    marker = "All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/).\n\n"
    section = f'''## [{VERSION}] - 2026-08-19\n\n### Added\n\n- Add a dedicated MP3000/1511 `active_alarm_names` sensor so localized active alarm text is directly visible and usable.\n\n### Fixed\n\n- Decode MP3000/1511 `0x07EF` raw `4000` with candidate factor `0.01`, exposing `40.00 %/Hz`.\n- Keep stable `A001`–`A224` identifiers internal/diagnostic and remove them from user-facing unknown alarm text.\n- Refresh web/entity counts to 105 maximum, 56 enabled by default and 49 advanced/disabled by default.\n- Remove stale public references to the discarded MP3000 power-level candidate.\n\n### Changed\n\n- Keep technical entity IDs stable in English while display names and alarm text remain localized in all eight supported languages.\n- Preserve beta1 logger RSSI/A1/21 diagnostics and beta2 localization/removal fixes.\n- Keep newly observed reactive-mode, GFCI, calibration and anti-reflux correlations in the research backlog only.\n- Verify HACS metadata and Home Assistant local icon/logo assets.\n\n### Safety\n\n- All MP3000 alarm and diagnostic access remains local and read-only.\n- No inverter configuration, protection, country/profile or control write is added.\n\n'''
    text = must_replace(text, marker, marker + section, p)
write(p, text)

# Version-pinned tests.
for tp in Path("tests").glob("test_*.py"):
    t = tp.read_text(encoding="utf-8").replace("1.5.1-beta.2", VERSION)
    tp.write_text(t, encoding="utf-8")

# HACS metadata and local brand assets.
hacs = json.loads(read("hacs.json"))
if hacs != {"name": "TSUN Local", "homeassistant": "2026.3.0"}:
    raise SystemExit(f"Unexpected hacs.json: {hacs}")


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise SystemExit(f"Invalid PNG: {path}")
    return struct.unpack(">II", data[16:24])


for name in ("icon.png", "icon@2x.png", "logo.png", "logo@2x.png"):
    path = Path("custom_components/tsun_local/brand") / name
    if not path.is_file():
        raise SystemExit(f"Missing brand asset: {path}")
    width, height = png_size(path)
    if width < 128 or height < 128:
        raise SystemExit(f"Brand asset too small: {path}={width}x{height}")
    print(f"Brand OK: {path} {width}x{height}")

# Requested public-web cleanup guards.
index = read("docs/index.html")
for forbidden in (
    "Evidence stays explicit",
    "Country value: 8, not 1008",
    "Country mapping attribution and validation",
    "Connection/reconnection pair stays documentation-only",
    "power-level candidate",
    "Unidentified inverter alarm (A030)",
):
    if forbidden in index:
        raise SystemExit(f"Stale public website text remains: {forbidden}")
entities = read("docs/entities.html")
if "4000 × 0.01 = 40.00 %/Hz" not in entities:
    raise SystemExit("Missing corrected coefficient on entity web page")
if "Active alarm names" not in entities:
    raise SystemExit("Missing dedicated active alarm names on entity web page")
