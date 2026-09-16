<p align="center">
  <a href="https://github.com/jptstar/tsun-local/blob/main/README.md">English</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_FR.md">Français</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_DE.md">Deutsch</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_NL.md">Nederlands</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_IT.md">Italiano</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_ES.md">Español</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_PL.md">Polski</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/main/docs/README_ZH.md">简体中文</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon%402x.png" width="160" alt="TSUN Local Home Assistant integration for TSUN microinverters">
</p>

<h1 align="center">TSUN Local — Home Assistant integration for TSUN microinverters</h1>
<h3 align="center">Your inverter. Your network. Your data.</h3>
<p align="center"><strong>Automatic discovery · Local · Read-only · No cloud · No proxy</strong></p>
<p align="center">Open-source HACS integration for direct local monitoring of compatible TSUN solar microinverters in Home Assistant.<br><strong>1.6.2</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="https://github.com/jptstar/tsun-local"><img alt="GitHub stars" src="https://img.shields.io/github/stars/jptstar/tsun-local?style=flat&logo=github&label=Stars"></a>
  <a href="LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

<p align="center">
  <a href="https://jptstar.github.io/tsun-local/"><strong>Project website</strong></a> ·
  <a href="https://jptstar.github.io/tsun-local/entities.html"><strong>Entity reference</strong></a> ·
  <a href="https://jptstar.github.io/tsun-local/test-your-inverter.html"><strong>Test your inverter</strong></a>
</p>

---

## Compatibility

**Home Assistant 2026.3.0 or later.** Compatibility is determined primarily by the detected local protocol family, not only by the commercial model name.

| Protocol | Family | Validated hardware | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validated** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MS300** · **TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2** | ✅ **Validated** |
| **1097** | GEN4 | **Sunology PLAY2 (GEN4)** | ✅ **Validated** |

> [!TIP]
> **Not listed does not mean unsupported.** If TSUN Local detects a supported protocol, the inverter may already work even when its commercial model has not yet been independently validated.

<details>
<summary><strong>Likely compatible models by protocol</strong></summary>

- **1511 — likely compatible:** `TSOL-MP2250` · `TSOL-MS3000`
- **02B0 — likely compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800` · corresponding `-D` variants
- **1097 — likely compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

</details>

Dedicated compatibility pages:

- [TSOL-MP3000 / TITAN](https://jptstar.github.io/tsun-local/tsol-mp3000-home-assistant.html)
- [TSOL-MS300](https://jptstar.github.io/tsun-local/tsol-ms300-home-assistant.html)
- [TSOL-MX500](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html)
- [TSOL-MS800](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html)
- [TSOL-MS2000](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html)
- [Sunology PLAY2 — 02B0 and GEN4 / 1097](https://jptstar.github.io/tsun-local/sunology-play2.html)

📚 [Full entity reference by protocol](docs/ENTITIES.md) · [MP3000 field validation](docs/MP3000_FIELD_VALIDATION.md)

---

## What TSUN Local exposes

| | Home Assistant data |
|---|---|
| ☀️ **PV** | Voltage · Current · Power · Daily energy · Total energy for each detected input |
| ⚡ **AC** | Voltage · Current · Frequency · Power · Daily energy · Total energy |
| 🚨 **Alarms** | Alarm state · Active alarm count · Localized readable alarm names |
| 📡 **Communication** | Online state · Last response · Failure count · Adaptive polling interval |
| 🧩 **Device information** | Firmware · Logger information · Detected PV inputs |
| 🛡️ **Advanced diagnostics** | Read-only protocol diagnostics, disabled by default where appropriate |

TSUN Local preserves stable protocol-position alarm codes while showing readable descriptions. **1511 exposes 224 catalogue positions; 02B0 and 1097 expose 64 positions each.**

**Adaptive polling** automatically slows communication after failures and during offline/night periods so one unavailable inverter does not unnecessarily block normal monitoring.

---

## Installation

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Add TSUN Local to HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

Or add `https://github.com/jptstar/tsun-local` as **HACS → Custom repositories → Integration**, install **TSUN Local**, restart Home Assistant, then add **TSUN Local** from **Settings → Devices & services**.

### Manual

Copy `custom_components/tsun_local` to `/config/custom_components/`, restart Home Assistant, then add the integration from **Settings → Devices & services**.

---

## How it works

```text
TSUN microinverter
       │
       │ Local network
       ▼
   TSUN Local
       │
       ▼
 Home Assistant
```

**No cloud in the data path. No proxy. No remote runtime service. No inverter configuration writes.**

---

## 🔬 Validate another TSUN model

The diagnostic is privacy-safe and **strictly read-only**. Official public distribution is intentionally simple:

| Package | Platform | Download |
|---|---|---|
| **Windows diagnostic** | Windows x86_64 · no Python required | [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe) · [SHA-256](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe.sha256) |
| **Full Python diagnostic** | Windows · macOS · Linux · Python 3.10+ | [TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip) · [SHA-256](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip.sha256) |

The full Python package contains the supported command-line diagnostic and its required files. There are **no separate official macOS or Linux native binaries** in the public distribution.

Typical full-Python launch after extracting the package:

```bash
python3 tsun_diagnostic_cli.py --full
```

On Windows, `py tsun_diagnostic_cli.py --full` can be used instead.

The workflow is the same:

1. **Disable TSUN Local** for the affected logger.
2. **Run the diagnostic**.
3. **Direct report upload** — recommended; explicit consent is mandatory.
4. **Manual e-mail report** — optional fallback only.

The tester name/pseudonym and inverter model/quantity rows can be saved locally. Consent is never remembered. Submitted reports remain anonymized and the uploader returns a `TSL-...` receipt with a private-token link that lets the tester inspect the submitted report.

`tsun_dump.py` remains available as a **compatibility / advanced fallback**, but the full Python diagnostic package is the normal cross-platform Python distribution.

📦 [Rolling diagnostic release](https://github.com/jptstar/tsun-local/releases/tag/diagnostic-latest) · 📚 [Hardware diagnostic guide](docs/HARDWARE_DUMP.md) · 📋 [Direct-upload validation protocol](docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md) · 🌐 [Public diagnostic page](https://jptstar.github.io/tsun-local/test-your-inverter.html)

### Sunology PLAY2

**Sunology PLAY2 is validated on real Home Assistant hardware** through both the local **02B0 / GEN3 Plus** path and the **1097 / GEN4** path.

- Automatic discovery and normal TSUN Local setup are confirmed independently.
- The commercial PLAY2 name spans more than one local hardware generation.
- The detected **02B0** or **1097** protocol is authoritative.

📚 [PLAY2 local protocol research](docs/PLAY2_LOCAL_RESEARCH.md) · 🔬 [Optional read-only PLAY2 probe](tools/tsun_play2_probe.py)

---

## Validation policy

TSUN Local separates confirmed hardware support from experimental protocol research. Functional names and model support are labelled as validated only after repeatable checks on real hardware. A plausible register value is evidence, not proof; experimental mappings remain labelled until independently confirmed.

If an unlisted inverter detects `1511`, `02B0` or `1097`, let TSUN Local run and check the discovered entities. Useful compatibility feedback includes the exact inverter model, detected protocol, firmware, PV-input count and whether the main values are plausible.

---

## Credits

TSUN Local is an independent, unofficial community project. Public protocol research and real-hardware testers are credited separately so the README stays focused on installation and compatibility.

**[Full contributors & credits →](https://jptstar.github.io/tsun-local/contributors.html)**

Created and maintained by **Jean-Philippe TESTART · `jptstar`** for the Home Assistant community.

---

## License

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distributed under **GNU General Public License v3.0 or later**. See [LICENSE](LICENSE).
