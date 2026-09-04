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
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon%402x.png" width="160" alt="TSUN Local Home Assistant integration for TSUN micro-inverters">
</p>

<h1 align="center">TSUN Local — Home Assistant integration for TSUN micro-inverters</h1>
<h3 align="center">Your inverter. Your network. Your data.</h3>
<p align="center"><strong>Local. Read-only. No cloud. No proxy.</strong></p>
<p align="center">Open-source HACS integration providing direct local access to compatible TSUN solar micro-inverters in Home Assistant.<br><strong>1.6.0</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

<p align="center"><a href="https://jptstar.github.io/tsun-local/"><strong>Project website</strong></a></p>


---

## Compatibility

**Home Assistant 2026.3.0 or later.**

| Protocol | Family | Validated hardware | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validated** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MX500** · **TSOL-MS800** · **Sunology PLAY2** | ✅ **Validated** |
| **1097** | GEN3 / GEN3 PLUS | — | 🧪 **Experimental** |

> [!TIP]
> **Not listed does not mean unsupported.** TSUN Local identifies compatibility primarily from the detected local protocol, not only from the commercial model name.

<details>
<summary><strong>Likely compatible models by protocol</strong></summary>

- **1511 — Likely compatible:** `TSOL-MP2250` · `TSOL-MS3000` (TITAN)
- **02B0 — Likely compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000` · corresponding `-D` variants
- **1097 — Likely compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

</details>

📚 **[MP3000 / TITAN validation](docs/MP3000_FIELD_VALIDATION.md)**

📚 **[TSOL-MX500 Home Assistant](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html)** · **[TSOL-MS800 Home Assistant](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html)**

**New in 1.6.0:** **Adaptive polling** is enabled by default and automatically adjusts the read interval after communication failures: 20 s normal, 30 s after an error and 300 s offline/night.

📚 **[Full entity reference](docs/ENTITIES.md)**

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Add TSUN Local to HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

---


## At a glance

| | What TSUN Local exposes |
|---|---|
| ☀️ **PV** | Voltage · Current · Power · Daily energy · Total energy |
| ⚡ **AC** | Voltage · Current · Frequency · Power · Daily energy · Total energy |
| 🚨 **Diagnostics** | Active alarms · Communication · Logger information |
| 🛡️ **Advanced** | Grid protection · Firmware · Inverter diagnostics · Experimental field-validation data |
| 🔒 **Safety** | Read-only · No inverter configuration writes |

📚 **[Full entity reference by protocol](docs/ENTITIES.md)**


---


## 🚨 Alarm catalogues

TSUN Local keeps the Home Assistant alarm interface compact while preserving every alarm-bit position used by each supported protocol. **1511 exposes 224 catalogue positions; 02B0 and 1097 expose 64 positions each.**

Every active alarm is presented as `Description (PROTOCOL-Axxx)`, including alarms whose functional meaning is already known. Unknown positions remain visible with neutral localized wording, for example `Unidentified inverter alarm (02B0-A006)`.

Home Assistant exposes one **Inverter alarm** state, an **Active alarms** count and an **Active alarm names** sensor for 1511, 02B0 and 1097. **Active alarm names are localized clear-text descriptions with stable protocol-position codes** (for example `Grid undervoltage (02B0-A014)`). On Sunology PLAY2, the four raw 02B0 ERR words remain available as disabled-by-default diagnostics.


---


## 🛡️ Advanced diagnostics

Advanced entities are intentionally **disabled by default**. They include protocol-dependent grid-protection values, firmware and inverter diagnostics, plus selected experimental field-validation values.

To enable one:

**Settings → Devices & services → TSUN Local → Device → Entities → Disabled entities**

Experimental semantic mappings remain explicitly marked until independently validated. No inverter configuration writes are implemented.

Communication logs and exported diagnostics can include only the first three alphanumeric characters of the micro-inverter serial number (for example `Y47`) to distinguish devices while keeping the complete serial number redacted.

📚 **[MP3000 field-validation evidence](docs/MP3000_FIELD_VALIDATION.md)**
📚 **[Full entity reference](docs/ENTITIES.md)**


---


## Installation

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Add TSUN Local to HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

Or add `https://github.com/jptstar/tsun-local` as **HACS → Custom repositories → Integration**, install **TSUN Local**, then restart Home Assistant.

### Manual

Copy `custom_components/tsun_local` to `/config/custom_components/`, restart Home Assistant, then add **TSUN Local** from **Settings → Devices & services**.


---


## How it works

```text
TSUN inverter
     │
     │ Local network
     ▼
 TSUN Local
     │
     ▼
Home Assistant
```

**No cloud in the data path. No proxy. No remote runtime service. No inverter configuration writes.**

Direct local polling only.


---


## 🔬 Validate another TSUN model

TSUN Local includes a standalone, privacy-safe and **strictly read-only** hardware dump tool.

**⬇️ [Download `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

Python 3.10+ is enough.

macOS / Linux:

```bash
cd ~/Downloads
python3 tsun_dump.py --full
```

Windows:

```powershell
py tsun_dump.py --full
```

The tool can discover compatible TSUN loggers, detect supported protocol families and create one privacy-safe JSON dump per device. No inverter write operation is implemented.

For VLANs, targeted discovery, before/after comparisons and advanced validation:

📚 **[Hardware Validation Dump Tool guide](docs/HARDWARE_DUMP.md)**


### Sunology PLAY2

**Sunology PLAY2 is validated on real Home Assistant hardware** through the local 02B0 / Solarman V5 path.

- Automatic discovery and normal TSUN Local setup confirmed independently.
- Local and read-only: no cloud or inverter configuration writes.
- The exact MX400/MX450/MX500 hardware variant remains intentionally unspecified; the detected **02B0** protocol is authoritative.

📚 **[PLAY2 research details](docs/PLAY2_LOCAL_RESEARCH.md)** · 🔬 **[Optional read-only PLAY2 probe](tools/tsun_play2_probe.py)**

---


## Test an unlisted inverter

If TSUN Local detects `1511`, `02B0` or `1097`, let it run and check the discovered entities.

Useful compatibility feedback includes the exact inverter model, detected protocol, firmware version, number of PV inputs and which entities return plausible values.

> [!TIP]
> **Your inverter could become the next validated model.**


---


## Validation policy

TSUN Local separates confirmed hardware support from experimental protocol research.

Functional names and model support are labelled as validated only after repeatable checks on real hardware. A value that merely matches an expected profile is treated as evidence, not proof; experimental mappings remain labelled until an independent observation can distinguish them.


---

## Contributions & credits

TSUN Local benefits from public protocol research and independent hardware testing. These credits describe reference work and validation only; they do not imply affiliation or endorsement.

- **David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — independent public cross-reference used during selected Solarman / 02B0 register research.
- **Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — public GEN3 / 1097 protocol and country/profile research used during experimental validation.
- **TheSmartGerman** — real-device testing that revealed the additional 1097 protocol family.
- **dca31** — independent Sunology PLAY2 validation through the normal TSUN Local Home Assistant flow.
- **Kmotr** — independent TSOL-MS800 validation with TSUN Local and an anonymized Home Assistant diagnostic.

📚 **[Full contributors & credits](docs/contributors.html)**

---


## Project

> [!IMPORTANT]
> **Unofficial community project.** TSUN Local is independent and is not developed, approved, endorsed or maintained by TSUN.

Created and maintained by **Jean-Philippe TESTART · `jptstar`**
*Developed and shared for fun, technical curiosity and the Home Assistant community.*


---


## License

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distributed under **GNU General Public License v3.0 or later**. See [LICENSE](LICENSE).
