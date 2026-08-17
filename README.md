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

<!-- [Français](docs/README_FR.md) [Deutsch](docs/README_DE.md) **1.4.1** -->

<p align="center">
  <img src="custom_components/tsun_local/brand/icon@2x.png" width="160" alt="TSUN Local Home Assistant integration for TSUN micro-inverters">
</p>

<h1 align="center">TSUN Local — Home Assistant integration for TSUN micro-inverters</h1>
<h3 align="center">Your inverter. Your network. Your data.</h3>
<p align="center"><strong>Local. Read-only. No cloud. No proxy.</strong></p>
<p align="center">Open-source HACS integration providing direct local access to compatible TSUN solar micro-inverters in Home Assistant.<br><strong>1.4.1</strong></p>

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
| **02B0** | GEN3 PLUS · **TSOL-MX500** | ✅ **Validated** |
| **1097** | GEN3 | 🧪 **Experimental** |

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
| 🚨 **Diagnostics** | Alarms · Communication · Logger information |
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
| 🚨 **Diagnostics** | Inverter alarms |
| 🛡️ **Advanced** | Grid-protection thresholds and timing diagnostics · Inverter temperature · Inverter ambient temperature · Power level (candidate) |

### 02B0 · GEN3 PLUS — ✅ Validated

**✅ Validated**  
`TSOL-MX500`

**🔎 Likely compatible**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Corresponding `-D` variants may also be compatible where applicable.

> [!NOTE]
> Public GEN3 PLUS research generally associates these devices with the **Y17 / Y47** serial-number family. This is useful for distinguishing models whose names also exist in older GEN3 variants.

| | Available data |
|---|---|
| ☀️ **PV** | Dynamic PV-input detection · Voltage · Current · Power · Energy |
| ⚡ **AC** | Voltage · Current · Frequency · Power · Energy |
| 🚨 **Diagnostics** | Inverter alarms |
| 🛡️ **Advanced** | Grid-protection diagnostics · Power level (%) |

### 1097 · GEN3 — 🧪 Experimental

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

## TSUN Local 1.4

### A wider TSUN Local

Version 1.4 moves TSUN Local from individual known models toward **protocol-family compatibility**.

| | |
|---|---|
| 🔌 | **1511 · 02B0 · 1097** |
| 🔍 | Automatic protocol identification |
| ☀️ | Progressive / dynamic PV-input detection |
| 📊 | Expanded local telemetry |
| 🛡️ | Advanced read-only diagnostics |
| 🌍 | 8 languages |
| 🧪 | Easier testing of new TSUN models |

---

## Reverse engineering & validation

The 1511 and 02B0 implementations are developed through **independent local protocol analysis, real-device observation and hardware validation**.

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
