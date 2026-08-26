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
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon%402x.png" width="160" alt="TSUN Local Home Assistant integration for TSUN and Sunology PLAY2 micro-inverters">
</p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Plug-and-play local solar monitoring for Home Assistant</h3>
<p align="center"><strong>Automatic discovery · Local · Read-only · No cloud · No proxy</strong></p>
<p align="center">Direct local access to compatible TSUN micro-inverters and the <strong>Sunology PLAY2</strong>.<br><strong>1.5.2</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="Add TSUN Local to HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><a href="https://jptstar.github.io/tsun-local/"><strong>Project website</strong></a> · <a href="https://jptstar.github.io/tsun-local/sunology-play2.html"><strong>Sunology PLAY2</strong></a> · <a href="docs/ENTITIES.md"><strong>Entities</strong></a></p>

---

## Install it. Add it. TSUN Local finds the inverter.

TSUN Local is designed to make local solar monitoring feel like a native Home Assistant integration rather than a protocol project.

1. Install **TSUN Local** through HACS.
2. Restart Home Assistant and add **TSUN Local** from **Settings → Devices & services**.
3. On supported LAN setups, TSUN Local discovers the logger, identifies the supported protocol family and creates the device automatically.

**No IP address to enter in the normal automatic flow. No proxy to deploy. No cloud account required for the data path. No protocol selector to configure.**

Manual and targeted discovery remain available for unusual VLAN or network layouts.

---

## ✅ Sunology PLAY2 is now validated

A real **Sunology PLAY2** has completed the normal TSUN Local / Home Assistant installation successfully. The device was **detected automatically and quickly** by the integration during an independent community test.

The validated PLAY2 path is:

```text
Sunology PLAY2
  → LSW5BLE logger
  → TCP 8899
  → Solarman V5
  → sensor list 0x02B0
  → Modbus RTU FC03
  → TSUN Local
  → Home Assistant
```

Field-tested logger firmware: `LSW5BLE_17_02B0_1.08-D1`.

The dedicated PLAY2 probe was useful to identify the transport during research, but **ordinary PLAY2 users should start with the normal TSUN Local integration and automatic discovery**.

📚 **[Sunology PLAY2 local compatibility details](docs/PLAY2_LOCAL_RESEARCH.md)**

---

## Compatibility

**Home Assistant 2026.3.0 or later.**

| Protocol | Family / validated hardware | Status |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Validated |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500 · Sunology PLAY2** | ✅ Validated |
| **1097** | GEN3 / GEN3 PLUS | 🧪 Experimental |

**Likely compatible 1511 / 02B0 models:** `TSOL-MP2250`, `TSOL-MS3000` (TITAN generation), `TSOL-MX450`, `TSOL-MX800`, `TSOL-MX1000`, `TSOL-MX3000`, `TSOL-MS800`, `TSOL-MS1600`, `TSOL-MS1800`, `TSOL-MS2000` and corresponding `-D` variants where applicable.

**Experimental 1097 candidates:** `TSOL-MS300`, `TSOL-MS350`, `TSOL-MS400`, `TSOL-MS600`, `TSOL-MS700`, `TSOL-MS800`, `TSOL-MS3000`, `TSOL-MX3000D`.

> [!NOTE]
> A commercial model name can span several hardware or logger generations. **The detected local protocol is authoritative for TSUN Local compatibility.**

---

## What you get in Home Assistant

| | TSUN Local exposes |
|---|---|
| ☀️ **PV** | Voltage · Current · Power · Daily energy · Total energy |
| ⚡ **AC** | Voltage · Current · Frequency · Power · Daily energy · Total energy |
| 🚨 **Alarms** | Inverter alarm · Active alarm count · Human-readable active alarm names where supported |
| 📡 **Communication** | Online state · Last successful communication · Duration · Failures |
| 🧩 **Device** | Firmware · logger information · detected PV inputs |
| 🛡️ **Advanced** | Read-only grid protection and validation diagnostics, disabled by default |

PV inputs are created dynamically as they are detected instead of forcing a fixed inverter layout.

📚 **[Full entity reference by protocol](docs/ENTITIES.md)**  
🌐 **[Visual entity reference](https://jptstar.github.io/tsun-local/entities.html)**

---

## 🚨 Clear-text alarms — 1.5.3 beta

The current **1.5.3 beta** extends the compact alarm interface across **1511, 02B0 and 1097**.

Instead of exposing only raw bitfields, active alarms can be presented as readable localized text while preserving a stable protocol-position code for diagnosis:

```text
Grid undervoltage (02B0-A014)
PV1 input voltage too low (1511-A137)
Unidentified inverter alarm (1097-A041)
```

Known alarms get a clear functional description. Unknown or reserved positions remain visible with neutral wording rather than a guessed meaning.

- **1511:** 224 catalogue positions
- **02B0:** 64 catalogue positions
- **1097:** 64 catalogue positions
- English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese

The normal Home Assistant interface stays compact: **Inverter alarm**, **Active alarms** and **Active alarm names**. Complete raw alarm words remain available as disabled-by-default diagnostics.

---

## Read-only by design

TSUN Local performs local polling only.

- no inverter configuration writes;
- no grid-protection writes;
- no provisioning changes;
- no remote runtime service;
- no cloud or proxy in the Home Assistant data path.

Advanced experimental mappings remain explicitly labelled until independently validated.

---

## Installation

### HACS

Use the button above, or add:

`https://github.com/jptstar/tsun-local`

as **HACS → Custom repositories → Integration**, install **TSUN Local**, restart Home Assistant, then add the integration from **Settings → Devices & services**.

### Manual

Copy `custom_components/tsun_local` to `/config/custom_components/`, restart Home Assistant, then add **TSUN Local**.

---

## Test another inverter

If your inverter is not listed, TSUN Local may still work when it exposes `1511`, `02B0` or `1097`.

The repository includes a privacy-safe, strictly read-only validation tool:

**[`tools/tsun_dump.py`](tools/tsun_dump.py)**

Useful compatibility feedback includes the exact model or OEM brand, detected protocol, firmware version, number of PV inputs and whether the exposed AC/PV values look plausible.

> [!TIP]
> **Your inverter could become the next validated model.**

---

## Contributions

TSUN Local benefits from public protocol research and independent community hardware testing.

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — public GEN3 / 1097 protocol research used as a reference for selected experimental mappings.
- **TheSmartGerman** — real-device compatibility feedback.
- **dca31** — independent Sunology PLAY2 installation and Home Assistant compatibility validation.

---

## Project

> [!IMPORTANT]
> **Unofficial community project.** TSUN Local is independent and is not developed, approved, endorsed or maintained by TSUN or Sunology.

Created and maintained by **Jean-Philippe TESTART · `jptstar`**  
*Developed and shared for fun, technical curiosity and the Home Assistant community.*

Distributed under **GNU GPL v3.0 or later**. See [LICENSE](LICENSE).
