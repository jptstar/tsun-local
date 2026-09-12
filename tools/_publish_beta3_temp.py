from __future__ import annotations

import json
from pathlib import Path
import subprocess

BASE_SHA = "46180dd2dd64d71d4c414dab453e765781f2a6a5"
VERSION = "1.6.2-beta.3"

subprocess.run(["git", "fetch", "origin", "main", "--tags"], check=True)
subprocess.run(["git", "checkout", "--detach", BASE_SHA], check=True)

manifest_path = Path("custom_components/tsun_local/manifest.json")
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
manifest["version"] = VERSION
manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

changelog_path = Path("CHANGELOG.md")
changelog = changelog_path.read_text(encoding="utf-8")
section = """## [1.6.2-beta.3] - 2026-09-12

### Changed since beta.2

- Reduce Home Assistant Activity noise across runtime protocols `1511`, `02B0` and `1097`.
- Publish the user-facing `communication_last_success` timestamp at most every five minutes while retaining the exact last-success timestamp in integration diagnostics.
- Hide `communication_last_success` and raw `*_raw` diagnostic entities from normal UI visibility by default without removing them or disabling their underlying diagnostics. Existing installations receive a one-time visibility migration and users can reveal the entities again.
- Add the protocol-aware `country_profile` diagnostic. It preserves the numeric code and appends a native country/grid-profile name when known.
- For 1511 / MP3000, expose the evidence-backed mappings `2 (Deutschland)`, `6 (Polska)` and `8 (France)`; unknown codes remain numeric.
- Keep the established protocol-specific profile enumeration for `02B0` and `1097` rather than assuming that all families share one raw source register.

### Retained from beta.2

- Keep validated runtime protocol detection across `1511`, `1097` and `02B0` with firmware used only as a priority hint.
- Keep MP3000 / 1511 low-solar status `1511-A030` localized and non-fault when it is the only active bit.
- Keep validated 1097 / GEN4 wording and transparent TSUN Local brand assets.
- Keep experimental `3026` diagnostic-only and excluded from runtime automatic detection.
- Keep all inverter access local and strictly read-only.

### Validation

- Full Unit tests, HACS repository validation and Home Assistant Hassfest are required by the beta publication workflow before the release is created.

"""
marker = (
    "All notable changes to this project are documented here. "
    "The project follows [Semantic Versioning](https://semver.org/).\n\n"
)
if f"## [{VERSION}]" not in changelog:
    if marker not in changelog:
        raise SystemExit("Changelog header marker not found")
    changelog = changelog.replace(marker, marker + section, 1)
    changelog_path.write_text(changelog, encoding="utf-8")

notes = Path("docs/releases") / f"{VERSION}.md"
notes.write_text(
    """# TSUN Local 1.6.2-beta.3

This beta focuses on a much cleaner Home Assistant Activity view and adds protocol-aware country/grid-profile presentation.

## Activity cleanup

- Applies consistently to runtime protocols **1511, 02B0 and 1097**.
- `communication_last_success` is still available, but its user-facing timestamp changes at most once every five minutes instead of every poll.
- The exact last successful poll time is still retained in TSUN Local diagnostics.
- `communication_last_success` and raw `*_raw` diagnostics are hidden from normal Home Assistant UI visibility by default. They are not deleted and can be revealed from entity settings when needed.
- Existing installations receive this visibility cleanup once; if a user later chooses to reveal an entity, TSUN Local does not hide it again on every restart.
- Meaningful states stay visible: online/offline, adaptive polling state, operating state, inverter alarm and decoded active alarm names.

## Country / grid profile

A new diagnostic entity uses a stable English ID, `country_profile`, and presents the raw protocol value as `code (native name)` when a mapping is known.

For **1511 / MP3000**, current evidence supports:

- `2 (Deutschland)` — profile/cloud evidence;
- `6 (Polska)` — confirmed by three independent MP3000 hardware dumps;
- `8 (France)` — confirmed by two MP3000 hardware dumps.

Unknown 1511 values remain numeric instead of being guessed. The original raw value remains available separately for diagnostics.

For **02B0 and 1097**, TSUN Local uses their protocol-specific country/profile source and the established TSUN enumeration, with native/endonym country labels where practical.

## Retained from beta.2

- Conservative automatic protocol detection across validated runtime families `1511`, `1097` and `02B0`.
- Strict manual protocol selection and fail-closed ambiguity handling.
- MP3000 low-solar status `1511-A030` decoded as **Low solar input** and kept non-fault when it is the only active bit.
- Validated 1097 / GEN4 presentation.
- Transparent TSUN Local brand assets.
- Experimental `3026` remains diagnostic-only.

## Safety

TSUN Local remains local and strictly read-only. This beta adds no inverter configuration, protection-setting or control write operation.
""",
    encoding="utf-8",
)

subprocess.run(["git", "config", "user.name", "jptstar"], check=True)
subprocess.run(["git", "config", "user.email", "dev@jptstar.com"], check=True)
subprocess.run(
    [
        "git",
        "add",
        "custom_components/tsun_local/manifest.json",
        "CHANGELOG.md",
        str(notes),
    ],
    check=True,
)
subprocess.run(
    ["git", "commit", "-m", f"[beta-release] Publish TSUN Local {VERSION}"],
    check=True,
)
subprocess.run(
    [
        "git",
        "commit",
        "--allow-empty",
        "-m",
        f"[beta-release] Trigger TSUN Local {VERSION} publication",
    ],
    check=True,
)
subprocess.run(["git", "push", "--force", "origin", "HEAD:beta-1097"], check=True)
