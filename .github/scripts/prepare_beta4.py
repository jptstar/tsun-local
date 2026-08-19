from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = "1.5.1-beta.3"
NEW = "1.5.1-beta.4"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    (ROOT / path).write_text(content, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    content = read(path)
    if old not in content:
        raise SystemExit(f"Missing expected text in {path}: {old!r}")
    write(path, content.replace(old, new, 1))


def replace_all_if_present(path: str, old: str, new: str) -> None:
    content = read(path)
    if old in content:
        write(path, content.replace(old, new))


def load_json(path: str) -> dict:
    return json.loads(read(path))


def save_json(path: str, value: dict) -> None:
    write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


# Version metadata.
manifest = load_json("custom_components/tsun_local/manifest.json")
manifest["version"] = NEW
save_json("custom_components/tsun_local/manifest.json", manifest)

# MP3000 / 1511 firmware decoder and local register mapping.
path = "custom_components/tsun_local/protocols/protocol_1511.py"
content = read(path)
needle = "COUNTRY_PROFILE_REGISTER = 0x07D0\n"
insert = """COUNTRY_PROFILE_REGISTER = 0x07D0\nFIRMWARE_VERSION_REGISTERS = {\n    \"dsp_firmware_version\": 0x0BC0,\n    \"qcpu1_firmware_version\": 0x0E26,\n    \"qcpu2_firmware_version\": 0x0EEE,\n}\n"""
if needle not in content:
    raise SystemExit("Cannot insert MP3000 firmware register map")
content = content.replace(needle, insert, 1)
old_keys = '''        "ambient_temperature",\n        "country_profile_raw",\n'''
new_keys = '''        "ambient_temperature",\n        "country_profile_raw",\n        "dsp_firmware_version",\n        "qcpu1_firmware_version",\n        "qcpu2_firmware_version",\n'''
if old_keys not in content:
    raise SystemExit("Cannot extend TITAN diagnostic keys")
content = content.replace(old_keys, new_keys, 1)
needle = '''def _u32_type5(registers: dict[int, int], high_address: int) -> int:\n    \"\"\"Decode official byte-order type 5: high 16-bit register then low register.\"\"\"\n    return (registers[high_address] << 16) | registers[high_address + 1]\n\n\n'''
insert = needle + '''def firmware_version(value: int) -> str:\n    \"\"\"Decode a packed TSUN 16-bit firmware version.\"\"\"\n    raw = f"{value:04X}"\n    return f"V{raw[0]}.{raw[1]}.{raw[2:]}"\n\n\ndef decode_firmware_versions(registers: dict[int, int]) -> dict[str, str]:\n    \"\"\"Decode MP3000 DSP/QCPU firmware versions found in live 1511 blocks.\"\"\"\n    return {\n        key: firmware_version(registers[address])\n        for key, address in FIRMWARE_VERSION_REGISTERS.items()\n        if address in registers\n    }\n\n\n'''
if needle not in content:
    raise SystemExit("Cannot insert firmware_version decoder")
content = content.replace(needle, insert, 1)
content = content.replace(
    ") -> dict[str, float | int]:\n    \"\"\"Decode the validated AC and PV register map.\"\"\"",
    ") -> dict[str, float | int | str]:\n    \"\"\"Decode the validated AC and PV register map.\"\"\"",
    1,
)
needle = '''    }\n    if 0x0BCA in registers:\n'''
replace = '''    }\n    data.update(decode_firmware_versions(registers))\n    if 0x0BCA in registers:\n'''
if needle not in content:
    raise SystemExit("Cannot wire firmware decode into 1511 measurements")
content = content.replace(needle, replace, 1)
write(path, content)

# Sensor metadata: stable English IDs, localized display names.
path = "custom_components/tsun_local/sensor.py"
content = read(path)
needle = '''        "max_designed_power": "2042 (0x07FA)",\n'''
replace = '''        "max_designed_power": "2042 (0x07FA)",\n        "dsp_firmware_version": "3008 (0x0BC0)",\n        "qcpu1_firmware_version": "3622 (0x0E26)",\n        "qcpu2_firmware_version": "3822 (0x0EEE)",\n'''
if needle not in content:
    raise SystemExit("Cannot add 1511 firmware register addresses")
content = content.replace(needle, replace, 1)
needle = '''    TsunSensorDescription(\n        key="logger_firmware_version",\n        suggested_object_id="logger_firmware_version",\n        translation_key="logger_firmware_version",\n        entity_category=EntityCategory.DIAGNOSTIC,\n    ),\n'''
replace = needle + '''    TsunSensorDescription(\n        key="dsp_firmware_version",\n        suggested_object_id="dsp_firmware_version",\n        translation_key="dsp_firmware_version",\n        entity_category=EntityCategory.DIAGNOSTIC,\n    ),\n    TsunSensorDescription(\n        key="qcpu1_firmware_version",\n        suggested_object_id="qcpu1_firmware_version",\n        translation_key="qcpu1_firmware_version",\n        entity_category=EntityCategory.DIAGNOSTIC,\n    ),\n    TsunSensorDescription(\n        key="qcpu2_firmware_version",\n        suggested_object_id="qcpu2_firmware_version",\n        translation_key="qcpu2_firmware_version",\n        entity_category=EntityCategory.DIAGNOSTIC,\n    ),\n'''
if needle not in content:
    raise SystemExit("Cannot add firmware sensor descriptions")
content = content.replace(needle, replace, 1)
write(path, content)

# Home Assistant strings/translations.
names = {
    "en": {
        "dsp_firmware_version": "DSP firmware version",
        "qcpu1_firmware_version": "QCPU1 firmware version",
        "qcpu2_firmware_version": "QCPU2 firmware version",
    },
    "fr": {
        "dsp_firmware_version": "Version du firmware DSP",
        "qcpu1_firmware_version": "Version du firmware QCPU1",
        "qcpu2_firmware_version": "Version du firmware QCPU2",
    },
    "de": {
        "dsp_firmware_version": "DSP-Firmwareversion",
        "qcpu1_firmware_version": "QCPU1-Firmwareversion",
        "qcpu2_firmware_version": "QCPU2-Firmwareversion",
    },
    "es": {
        "dsp_firmware_version": "Versión de firmware DSP",
        "qcpu1_firmware_version": "Versión de firmware QCPU1",
        "qcpu2_firmware_version": "Versión de firmware QCPU2",
    },
    "it": {
        "dsp_firmware_version": "Versione firmware DSP",
        "qcpu1_firmware_version": "Versione firmware QCPU1",
        "qcpu2_firmware_version": "Versione firmware QCPU2",
    },
    "nl": {
        "dsp_firmware_version": "DSP-firmwareversie",
        "qcpu1_firmware_version": "QCPU1-firmwareversie",
        "qcpu2_firmware_version": "QCPU2-firmwareversie",
    },
    "pl": {
        "dsp_firmware_version": "Wersja firmware DSP",
        "qcpu1_firmware_version": "Wersja firmware QCPU1",
        "qcpu2_firmware_version": "Wersja firmware QCPU2",
    },
    "zh-Hans": {
        "dsp_firmware_version": "DSP 固件版本",
        "qcpu1_firmware_version": "QCPU1 固件版本",
        "qcpu2_firmware_version": "QCPU2 固件版本",
    },
}
strings = load_json("custom_components/tsun_local/strings.json")
for key, name in names["en"].items():
    strings["entity"]["sensor"][key] = {"name": name}
save_json("custom_components/tsun_local/strings.json", strings)
for locale, translated in names.items():
    path = f"custom_components/tsun_local/translations/{locale}.json"
    doc = load_json(path)
    for key, name in translated.items():
        doc["entity"]["sensor"][key] = {"name": name}
    save_json(path, doc)

# Entity/reference documentation.
path = "docs/ENTITIES.md"
content = read(path)
content = content.replace(OLD, NEW)
content = content.replace("**105 Home Assistant entities**", "**108 Home Assistant entities**")
content = content.replace("| Device and logger information | 5 | label SN, inverter SN, logger firmware, MAC address, Wi-Fi signal |", "| Device and logger information | 8 | label SN, inverter SN, logger/DSP/QCPU firmware, MAC address, Wi-Fi signal |")
content = content.replace("| **Total** | **105** | **56 enabled by default · 49 advanced/disabled by default** |", "| **Total** | **108** | **59 enabled by default · 49 advanced/disabled by default** |")
content = content.replace(
    "Only the logger firmware is currently exposed. FCPU, DSP, QCPU1 and QCPU2 firmware entities are intentionally not listed until a reliable local mapping has been confirmed.",
    "The logger, DSP, QCPU1 and QCPU2 firmware versions are exposed. FCPU remains intentionally absent because its local 1511 source register has not yet been identified.",
)
needle = "| `logger_firmware_version` | Logger firmware version | text | ✅ |\n"
replace = needle + "| `dsp_firmware_version` | DSP firmware version | text | ✅ |\n| `qcpu1_firmware_version` | QCPU1 firmware version | text | ✅ |\n| `qcpu2_firmware_version` | QCPU2 firmware version | text | ✅ |\n"
if needle not in content:
    raise SystemExit("Cannot add firmware rows to entity reference")
content = content.replace(needle, replace, 1)
needle = "- Register 3017 is exposed as **Inverter temperature** and register 3028 as **Inverter ambient temperature**, both decoded with `raw - 40 °C`.\n"
replace = needle + "- Packed 16-bit firmware words are decoded locally with `firmware_version()`: DSP `3008 / 0x0BC0 = 0x1172 → V1.1.72`, QCPU1 `3622 / 0x0E26 = 0x1154 → V1.1.54`, and QCPU2 `3822 / 0x0EEE = 0x1154 → V1.1.54`. FCPU is not guessed.\n"
if needle not in content:
    raise SystemExit("Cannot add firmware observation note")
content = content.replace(needle, replace, 1)
write(path, content)

# Public README and localized README version markers.
for path in ["README.md", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs").glob("README_*.md"))]:
    replace_all_if_present(path, OLD, NEW)

path = "README.md"
content = read(path)
content = content.replace(
    "| 🚨 **Diagnostics** | Inverter alarm · Active-alarm count and names |",
    "| 🚨 **Diagnostics** | Inverter alarm · Active-alarm count and names · DSP/QCPU firmware versions |",
)
content = content.replace("| | 1.5.1-beta.3 |", "| | 1.5.1-beta.4 |")
needle = "| 🚨 | **Dedicated Active alarm names** sensor exposes localized alarm text directly in Home Assistant |\n"
if needle in content:
    content = content.replace(needle, needle + "| 🧠 | **MP3000 firmware diagnostics** — DSP `V1.1.72`, QCPU1 `V1.1.54`, QCPU2 `V1.1.54` decoded from local 1511 words; FCPU remains unmapped |\n", 1)
write(path, content)

# Website and entity web page version/count refresh.
for path in ["docs/index.html", "docs/entities.html"]:
    content = read(path).replace(OLD, NEW)
    content = content.replace("1.5.1 BETA 3", "1.5.1 BETA 4")
    content = content.replace("1.5.1 beta 3", "1.5.1 beta 4")
    content = content.replace(">105<", ">108<")
    content = content.replace(">56<", ">59<")
    content = content.replace("105 Home Assistant entities", "108 Home Assistant entities")
    content = content.replace("105 MP3000 entities", "108 MP3000 entities")
    content = content.replace("56 enabled by default", "59 enabled by default")
    if path.endswith("entities.html"):
        marker = "<code>logger_firmware_version</code>"
        if marker in content and "dsp_firmware_version" not in content:
            # Add concise firmware rows after the existing logger firmware row by locating its table row.
            row_start = content.rfind("<tr", 0, content.find(marker))
            row_end = content.find("</tr>", content.find(marker)) + len("</tr>")
            if row_start >= 0 and row_end > row_start:
                extra = (
                    '\n              <tr><td><code>dsp_firmware_version</code></td><td>DSP firmware version</td><td>text</td><td>✅</td></tr>'
                    '\n              <tr><td><code>qcpu1_firmware_version</code></td><td>QCPU1 firmware version</td><td>text</td><td>✅</td></tr>'
                    '\n              <tr><td><code>qcpu2_firmware_version</code></td><td>QCPU2 firmware version</td><td>text</td><td>✅</td></tr>'
                )
                content = content[:row_end] + extra + content[row_end:]
    if path.endswith("index.html") and "DSP/QCPU firmware" not in content:
        marker = "Active alarm names"
        pos = content.find(marker)
        if pos >= 0:
            # Keep layout intact; append firmware detail to the nearest paragraph/cell text.
            content = content[:pos] + "DSP/QCPU firmware · " + content[pos:]
    write(path, content)

# Refined research backlog after the 2026-08-19 17:37 UTC dump.
write(
    "docs/PENDING_1.5.1.md",
    """# TSUN Local 1.5.1 research backlog

These MP3000/1511 correlations are intentionally **kept out of 1.5.1-beta.4 semantic Home Assistant entities** until independently validated by a controlled setting change or distinct hardware observation.

## Very strong — exact live/profile match

- `0x07F1` → Reactive mode candidate, live raw `0x0066`, profile `0066`. The surrounding 1511 sequence also mirrors the public 02B0/GEN3 parameter sequence (`1, 0x139C, 0x0FA0, temperature, 0x0066, 1000, 1024`).
- `0x07F2` → GFCI enable candidate, live raw `1000`, profile `1000`; also positionally corroborated by the same 02B0 sequence.
- `0x07F9` → Calibration K3 candidate, live raw `1003`, profile `1003`; the immediately preceding pair is `1024, 1024`, matching K1/K2 values.
- `0x080D` → Anti-current / anti-reflux delay candidate, live raw `10`, profile `10 s`, inside the adjacent zero-export cluster.

Evidence status remains: **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**.

## Strong but order-indeterminate

- `0x07F7` / `0x07F8` → Calibration K1 / K2 candidate pair, both live raw `1024`; K1 and K2 also both equal `1024` in the profile, so their individual order cannot be distinguished on this unit.

## Stronger than before

- `0x07ED = 1` is now the leading candidate for the **overfrequency-reduction enable/signal** because it sits immediately before the confirmed `0x07EE = 50.20 Hz` reduction threshold and `0x07EF = 40.00 %/Hz` coefficient, and the homologous public 02B0 sequence has the same leading `1` at this position.
- `0x0809 = 1` should no longer be treated as an equal reduction-signal candidate. Its position immediately before the anti-reflux/zero-export cluster makes it an unidentified enable/status flag; semantic assignment remains open.

## Very promising cluster

- `0x080B`–`0x080E` currently reads `3000, 0, 10, 0`. This matches the value set formed by zero-export injection power (`3000 W`), anti-current delay (`10 s`) and zero-valued anti-current/anti-reflux fields, but the individual zero-valued assignments remain ambiguous. `0x080D` is the distinctive member and is tracked separately above.

## Dynamic isolation candidate — do not name Rx/Ry yet

- `0x0BD2` previously read `60000`, which is compatible with `60.000 MΩ` at `×0.001 MΩ`; the latest low-power dump reads `44666`, compatible with `44.666 MΩ` at the same scale. This behaviour is more consistent with a **live insulation measurement** than a fixed 60 MΩ setting.
- The profile contains both Rx and Ry at `60.00 MΩ`, but there is not yet a second independently identified 1511 word proving which channel, if either, `0x0BD2` represents. Do not expose it as Rx or Ry yet.

No write command is implemented or required for this research backlog.
""",
)

# Cumulative beta4 release notes (prepared, not published by this script).
release_notes = """# TSUN Local 1.5.1-beta.4

TSUN Local 1.5.1-beta.4 consolidates the MP3000 alarm interface introduced in 1.5.0 with the logger/field-validation work from beta1, localization cleanup from beta2, active-alarm presentation from beta3, and local MP3000 firmware diagnostics added in beta4. The integration remains fully local and read-only.

## From 1.5.0 — complete MP3000 alarm interface

- All **224 MP3000 alarm positions** remain covered.
- **12 functional mappings** remain hardware-observed for PV input undervoltage and PV DSP fault across PV1 through PV6.
- The remaining positions stay active with neutral wording until independently confirmed.
- The fourteen complete raw alarm words remain available as advanced diagnostics, disabled by default.
- Alarm presentation remains localized in all eight supported TSUN Local languages.

## From 1.5.1-beta.1 — MP3000 diagnostics and logger Wi-Fi

- Logger Wi-Fi RSSI fallback continues to read `/status.html` when earlier pages are valid but do not contain RSSI.
- Ten read-only MP3000/TITAN A1/21 field-validation diagnostics remain available, disabled by default.
- The raw 1511 country/profile candidate remains an advanced diagnostic.
- No 224-entity alarm wall is created.

## From 1.5.1-beta.2 — localization cleanup

- The discarded MP3000 `output_coefficient_candidate` / Power level candidate remains removed.
- Technical entity IDs and unique IDs stay stable in English.
- Display-name translation coverage remains enforced in English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese.

## From 1.5.1-beta.3 — active alarm text and 0x07EF correction

- Dedicated `active_alarm_names` sensor exposes localized active alarm text directly in Home Assistant.
- Stable `A001`–`A224` identifiers remain internal/diagnostic rather than primary user-facing alarm text.
- MP3000 `0x07EF` raw `4000` is exposed as **40.00 %/Hz** using the `×0.01` candidate scale.
- Home Assistant 2026.3+ local icon/logo assets and HACS metadata remain in place.

## New in 1.5.1-beta.4 — MP3000 firmware diagnostics

- Add local **DSP firmware version** from `3008 / 0x0BC0`: `0x1172 → V1.1.72`.
- Add local **QCPU1 firmware version** from `3622 / 0x0E26`: `0x1154 → V1.1.54`.
- Add local **QCPU2 firmware version** from `3822 / 0x0EEE`: `0x1154 → V1.1.54`.
- Use the compact `firmware_version()` decoder for packed 16-bit TSUN version words.
- Keep **FCPU intentionally unexposed**: the expected version is known from the TSUN/Talent profile, but no local 1511 source register has yet been identified, so beta4 does not guess one.
- Refresh MP3000 documentation to **108 maximum entities**, **59 enabled by default**, **49 advanced/disabled by default**.
- Refine the research backlog without promoting the reactive-mode/GFCI/calibration/anti-reflux candidates to semantic Home Assistant entities. In particular, `0x07ED` is now the leading overfrequency-reduction signal candidate, while `0x0809` remains unidentified; `0x0BD2` is tracked as a dynamic insulation-measurement candidate rather than a fixed Rx/Ry setting.

## Compatibility

- **1511 / TITAN:** validated on TSOL-MP3000.
- **02B0 / GEN3 / GEN3 PLUS:** validated on TSOL-MX500.
- **1097 / GEN3 / GEN3 PLUS:** experimental.
- Home Assistant **2026.3.0 or later**.

## Safety

- All inverter data access remains local and read-only.
- Logger metadata uses local HTTP GET only.
- No inverter configuration, protection-setting, country/profile or control write is added.

## Validation

Beta4 is prepared on `beta-1097` for unit tests, HACS validation and Home Assistant hassfest before any prerelease tag is created.
"""
write("docs/releases/1.5.1-beta.4.md", release_notes)

# Changelog entry.
path = "CHANGELOG.md"
content = read(path)
entry = """## [1.5.1-beta.4] - 2026-08-19

### Added

- Add MP3000/1511 DSP, QCPU1 and QCPU2 firmware-version diagnostics from local packed 16-bit words.
- Add the reusable `firmware_version()` decoder for TSUN packed firmware values.

### Changed

- Keep FCPU unexposed until its local 1511 source register is identified.
- Refine the research backlog after a new low-power dump: keep reactive mode, GFCI, K1/K2/K3 and anti-reflux candidates out of semantic entities; promote `0x07ED` to the leading overfrequency-reduction signal candidate; track `0x0BD2` as a dynamic insulation-measurement candidate rather than a fixed 60 MΩ setting.
- Refresh MP3000 documentation to 108 maximum entities, 59 enabled by default and 49 advanced/disabled by default.

### Safety

- All new firmware reads reuse existing local 1511 telemetry blocks and remain read-only.
- No inverter configuration or control write is added.

"""
anchor = "## [1.5.1-beta.3]"
if anchor not in content:
    raise SystemExit("Cannot insert beta4 changelog")
content = content.replace(anchor, entry + anchor, 1)
write(path, content)

# Regression tests for the packed firmware decoder and register assignments.
write(
    "tests/test_mp3000_firmware_versions.py",
    '''"""Regression tests for MP3000 packed firmware-version diagnostics."""\n\nfrom custom_components.tsun_local.protocols.protocol_1511 import (\n    FIRMWARE_VERSION_REGISTERS,\n    TITAN_DIAGNOSTIC_KEYS,\n    decode_firmware_versions,\n    firmware_version,\n)\n\n\ndef test_firmware_version_decoder() -> None:\n    assert firmware_version(0x1172) == "V1.1.72"\n    assert firmware_version(0x1154) == "V1.1.54"\n    assert firmware_version(0x1304) == "V1.3.04"\n\n\ndef test_mp3000_firmware_registers() -> None:\n    assert FIRMWARE_VERSION_REGISTERS == {\n        "dsp_firmware_version": 0x0BC0,\n        "qcpu1_firmware_version": 0x0E26,\n        "qcpu2_firmware_version": 0x0EEE,\n    }\n    decoded = decode_firmware_versions(\n        {0x0BC0: 0x1172, 0x0E26: 0x1154, 0x0EEE: 0x1154}\n    )\n    assert decoded == {\n        "dsp_firmware_version": "V1.1.72",\n        "qcpu1_firmware_version": "V1.1.54",\n        "qcpu2_firmware_version": "V1.1.54",\n    }\n    assert set(decoded) <= TITAN_DIAGNOSTIC_KEYS\n''',
)

print(f"Prepared {NEW}")
