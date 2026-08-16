<p align="center">
  <img src="custom_components/tsun_local/brand/icon@2x.png" width="170" alt="TSUN Local">
</p>

<h1 align="center">TSUN Local</h1>

<p align="center">

[English](README.md) · [Français](docs/README_FR.md) · [Deutsch](docs/README_DE.md) · [Nederlands](docs/README_NL.md) · [Italiano](docs/README_IT.md) · [Español](docs/README_ES.md) · [Polski](docs/README_PL.md) · [简体中文](docs/README_ZH.md)

</p>

<h3 align="center">Your inverter. Your network. Your data.</h3>
<h2 align="center">Local. Read-only. No cloud. No proxy.</h2>

<p align="center"><strong>Direct local access for compatible TSUN micro-inverters in Home Assistant.</strong><br>**1.4.0-beta.8**</p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS Custom" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

<p align="center">Created and maintained by <strong>Jean-Philippe TESTART · <code>jptstar</code></strong><br><em>Built and shared for fun, technical curiosity and the Home Assistant community.</em></p>

> [!IMPORTANT]
> **Unofficial community project.** TSUN Local is independent and is not developed, approved, endorsed or maintained by TSUN.

---

## Your TSUN inverter may already work

TSUN Local communicates directly with compatible TSUN micro-inverters on your LAN and supports several local protocol families.

**Your exact model does not need to be listed to be compatible.**

| Protocol | Known hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Validated |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ Validated |
| **1097** | Compatible GEN3-family devices | 🧪 Experimental |

> **Not listed does not mean unsupported.**

If your inverter uses **1511, 02B0 or 1097**, try it.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Add TSUN Local to HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Install it. Let TSUN Local identify the protocol. See what your inverter exposes.</strong></p>

---

## What you get

### ☀️ PV
Voltage · Current · Power · Daily energy · Total energy

### ⚡ AC
Voltage · Current · Frequency · Power · Daily energy · Total energy

### 🚨 Diagnostics
Alarms · Logger information · Communication state

### 🛡️ Advanced diagnostics
Read-only grid and inverter parameters are exposed where supported. Advanced entities are **disabled by default** and can be enabled individually in Home Assistant.

- **1511:** complete grid-protection diagnostic map.
- **02B0:** complete grid-protection diagnostic map plus output coefficient.
- **1097:** protocol/inverter versions, inverter temperature, insulation impedance RX/RY, country/profile code and designed power where available.

**No inverter configuration writes are implemented.**

---

## Compatibility

**Home Assistant 2026.3.0 or later.**

### ✅ Validated on real hardware

| Model | Protocol | PV inputs |
|---|---|---:|
| **TSOL-MP3000** | 1511 | 6 |
| **TSOL-MX500** | 02B0 | 1 |

### 🔎 Worth trying

**1511 / TITAN**
- TSOL-MP2250
- TSOL-MS3000

**02B0 / GEN3 / GEN3 PLUS**
- MX400 / MX450
- MX800 / MX900 / MX1000
- MX2250
- MS300 / MS350 / MS400
- MS600 / MS700 / MS800
- MS1600 / MS1800 / MS2000
- corresponding `-D` variants where applicable

### 🧪 Experimental

**1097** support is available for testing and needs additional real-hardware validation.

> **Have another TSUN model? Try it. Your feedback can turn it into the next validated device.**

---

## Installation

### HACS
Use the button above, or add `https://github.com/jptstar/tsun-local` as a **Custom repository → Integration** in HACS, download **TSUN Local**, then restart Home Assistant.

### Manual
Copy `custom_components/tsun_local` to `/config/custom_components/`, restart Home Assistant, then add **TSUN Local** from **Settings → Devices & services**.

---

## How it works

- direct local polling;
- no external proxy;
- no TSUN cloud required for telemetry;
- no remote runtime service;
- read-only communication;
- automatic protocol identification where firmware provides a known protocol token;
- forced protocol probing available for compatibility testing.

---

## TSUN Local 1.4

Version 1.4 broadens TSUN Local from individual tested models toward **protocol-family compatibility**.

**1511 · 02B0 · 1097**

It brings automatic protocol identification, progressive PV-input detection, expanded local telemetry, advanced read-only diagnostics, multilingual entity names and easier testing of new TSUN models.

---

## Reverse engineering & validation

The 1511 and 02B0 implementations are developed through **independent local protocol analysis, real-device observation and hardware validation**.

The experimental 1097 mapping was informed by publicly available protocol research from **Stefan Allius / `s-allius/tsun-gen3-proxy`**, then adapted to TSUN Local for direct local use.

---

## License

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Distributed under the **GNU General Public License v3.0 or later**. See [LICENSE](LICENSE).
