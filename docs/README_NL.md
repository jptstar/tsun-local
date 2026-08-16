# TSUN Local 1.4.0

<p align="center">[English](../README.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [Nederlands](README_NL.md) · [Italiano](README_IT.md) · [Español](README_ES.md) · [Polski](README_PL.md) · [简体中文](README_ZH.md)</p>

### Jouw omvormer. Jouw netwerk. Jouw data.
## Lokaal. Alleen-lezen. Geen cloud. Geen proxy.

> **Jouw TSUN-omvormer werkt mogelijk al**  
> Niet vermeld betekent niet automatisch niet ondersteund.

| Protocol | Hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Gevalideerd op echte hardware |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ Gevalideerd op echte hardware |
| **1097** | GEN3 family | 🧪 Experimenteel |

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

**Installeer TSUN Local, laat het protocol herkennen en bekijk welke gegevens je omvormer aanbiedt.**

## Geavanceerde diagnostiek

Alleen-lezen net- en omvormerparameters zijn standaard uitgeschakeld en kunnen afzonderlijk in Home Assistant worden ingeschakeld.

- **1511:** grid protection diagnostics
- **02B0:** grid protection diagnostics + output coefficient
- **1097:** protocol/inverter versions, temperature, insulation impedance RX/RY, country/profile code and designed power

## Compatibiliteit

### ✅ Gevalideerd op echte hardware
- **TSOL-MP3000** — 1511 — 6 PV inputs
- **TSOL-MX500** — 02B0 — 1 PV input

### 🔎 Het proberen waard
MP2250 · MS3000 · MX400 · MX450 · MX800 · MX900 · MX1000 · MX2250 · MS300 · MS350 · MS400 · MS600 · MS700 · MS800 · MS1600 · MS1800 · MS2000 and corresponding `-D` variants where applicable.

### 🧪 1097 — Experimenteel

Heb je een ander TSUN-model? Probeer het: jouw apparaat kan het volgende gevalideerde model worden.

---

**Jean-Philippe TESTART (`jptstar`)** · Unofficial independent community project · GPL-3.0-or-later

De experimentele 1097-mapping is gebaseerd op openbaar protocolonderzoek van Stefan Allius / s-allius/tsun-gen3-proxy en aangepast voor TSUN Local.
