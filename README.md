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

<!-- [Français](docs/README_FR.md) [Deutsch](docs/README_DE.md) **1.5.0** -->

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon%402x.png" width="160" alt="TSUN Local Home Assistant integration for TSUN micro-inverters">
</p>

<h1 align="center">TSUN Local — Home Assistant integration for TSUN micro-inverters</h1>
<h3 align="center">Your inverter. Your network. Your data.</h3>
<p align="center"><strong>Local. Read-only. No cloud. No proxy.</strong></p>
<p align="center">Open-source HACS integration providing direct local access to compatible TSUN solar micro-inverters in Home Assistant.<br><strong>1.5.0</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

<p align="center"><a href="https://jptstar.github.io/tsun-local/"><strong>Project website</strong></a></p>

---

## Your TSUN inverter may already work

TSUN Local supports **three local TSUN protocol families**.

| Protocol | Family / validated reference | Status |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **Validated** |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ **Validated** |
| **1097** | GEN3 / GEN3 PLUS | 🧪 **Experimental** |

> [!TIP]
> **Not listed does not mean unsupported.** If your inverter uses **1511, 02B0 or 1097**, it may already work.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Add TSUN Local to HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Install it. Let TSUN Local identify the protocol. See what your inverter exposes.</strong></p>

---

## At a glance

| | What TSUN Local exposes |
|---|---|
| ☀️ **PV** | Voltage · Current · Power · Daily energy · Total energy |
| ⚡ **AC** | Voltage · Current · Frequency · Power · Daily energy · Total energy |
| 🚨 **Diagnostics** | Active alarm names · Communication · Logger information |
| 🛡️ **Advanced** | Grid protection · Inverter diagnostics · Disabled by default |
| 🔒 **Safety** | Read-only · No inverter configuration writes |

📚 **[Full entity reference by protocol](docs/ENTITIES.md)** — complete list of sensors, binary sensors and buttons exposed by **1511, 02B0 and 1097**.

---

## Compatibility

**Home Assistant 2026.3.0 or later.**

> [!NOTE]
> **✅ Validated** = confirmed on real TSUN Local hardware.  
> **🔎 Likely compatible** = the protocol family is supported, but this exact model has not yet been validated with TSUN Local.  
> **🧪 Experimental** = protocol support exists, but broader real-device validation is still needed.

### 1511 · TITAN — ✅ Validated

**✅ Validated**  
`TSOL-MP3000`

**🔎 Likely compatible**  
`TSOL-MP2250` · `TSOL-MS3000` *(TITAN generation)*

| | Available data |
|---|---|
| ☀️ **PV** | Up to 6 inputs · Voltage · Current · Power · Daily & total energy |
| ⚡ **AC** | Voltage · Current · Frequency · Power · Daily & total energy |
| 🚨 **Diagnostics** | Inverter alarm · Active-alarm count and names |
| 🛡️ **Advanced** | Grid-protection thresholds and timing diagnostics · Inverter temperature · Inverter ambient temperature · Power level (candidate) |

### 02B0 · GEN3 / GEN3 PLUS — ✅ Validated

**✅ Validated**  
`TSOL-MX500`

**🔎 Likely compatible**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Corresponding `-D` variants may also be compatible where applicable.

| | Available data |
|---|---|
| ☀️ **PV** | Dynamic PV-input detection · Voltage · Current · Power · Energy |
| ⚡ **AC** | Voltage · Current · Frequency · Power · Energy |
| 🚨 **Diagnostics** | Inverter alarms |
| 🛡️ **Advanced** | Grid-protection diagnostics · Power level (%) |

### 1097 · GEN3 / GEN3 PLUS — 🧪 Experimental

**🔎 Likely compatible**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

> [!NOTE]
> Public GEN3 research generally associates these devices with the **R17 / R47** serial-number family. Compatibility with TSUN Local protocol **1097** remains experimental until confirmed on more real hardware.

| | Available data |
|---|---|
| ☀️ **PV** | Standard PV telemetry |
| ⚡ **AC** | Standard inverter / AC telemetry |
| 🚨 **Diagnostics** | Available inverter diagnostics |
| 🛡️ **Advanced** | Protocol version · Inverter version · Temperature · Insulation RX/RY · Power level (experimental) · Country/profile raw value · Designed power |

> **🔎 Likely compatible does not mean validated.** It means TSUN Local already implements the relevant protocol family, making the device a strong compatibility candidate.

---

## 🚨 MP3000 alarm catalogue

TSUN Local now models every bit exposed by the MP3000 alarm words. **All 224 positions are included, counted and displayed when active.** No active position is discarded.

| Local catalogue | Positions | Status |
|---|---:|---|
| `A001`–`A064` | 64 inverter positions | Control-hardware validation required |
| `A065`–`A128` | 64 controller positions | Control-hardware validation required |
| `A129`–`A224` | 96 PV positions | 12 validated · 84 require control-hardware validation |

The **12 validated functional mappings** cover low PV input voltage and PV DSP faults for PV1 through PV6. The remaining **212 positions are fully operational catalogue entries**: each receives a stable neutral TSUN Local code and appears in Home Assistant if it becomes active. Its functional description is added only after physical validation on suitable control hardware.

Home Assistant shows one clear **Inverter alarm** state plus an **Active alarms** count and list. The 14 complete raw words remain available as disabled-by-default diagnostics, without creating 224 permanent entities.

Alarm wording is translated into all eight TSUN Local languages. These are independent TSUN Local translations based on the confirmed meanings; they are not presented as vendor-certified server wording.

---

## 🛡️ Advanced diagnostics

Advanced entities are intentionally **disabled by default**. This keeps the normal Home Assistant device page simple while still making deeper inverter information available when needed.

To enable one:

**Settings → Devices & services → TSUN Local → Device → Entities → Disabled entities**

No inverter configuration writes are implemented.

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

## Test another TSUN model

Your inverter does not have to be listed above.

If TSUN Local identifies one of these protocols:

```text
1511
02B0
1097
```

let it run and check what entities are discovered.

> [!TIP]
> **Your inverter could become the next validated model.** Useful feedback includes the exact model, detected protocol, number of PV inputs, firmware version and which entities return plausible values.

---

## TSUN Local 1.5.0

### Clear, complete MP3000 alarms

Version 1.5.0 adds a clean Home Assistant alarm interface while preserving every locally reported MP3000 alarm position.

| | |
|---|---|
| 🚨 | **224 alarm positions included** |
| ✅ | 12 hardware-validated functional mappings |
| 🔎 | 212 neutral entries awaiting physical validation |
| 📊 | Active-alarm count, names and stable local codes |
| 🛡️ | 14 complete raw words available but disabled by default |
| 🌍 | Alarm presentation in 8 languages |
| 🔒 | Fully local and read-only |

---

## Validation policy

Functional names and model support are labelled as validated only after repeatable checks on real hardware.

Compatibility candidates are intentionally labelled separately from validated hardware.

---

## Contributions

TSUN Local also benefits from community contributions:

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — public 1097 protocol research that informed the experimental mapping used by TSUN Local.
- **TheSmartGerman** — real-device testing and compatibility feedback for the **1511 TSOL-MP3000**, during which protocol **1097** was detected unintentionally.

---

## Project

> [!IMPORTANT]
> **Unofficial community project.** TSUN Local is independent and is not developed, approved, endorsed or maintained by TSUN.

Created and maintained by **Jean-Philippe TESTART · `jptstar`**  
*Built and shared for fun, technical curiosity and the Home Assistant community.*

---

## License

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distributed under the **GNU General Public License v3.0 or later**. See [LICENSE](LICENSE).
