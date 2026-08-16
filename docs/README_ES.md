# TSUN Local 1.4.0

<p align="center">[English](../README.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [Nederlands](README_NL.md) · [Italiano](README_IT.md) · [Español](README_ES.md) · [Polski](README_PL.md) · [简体中文](README_ZH.md)</p>

### Tu inversor. Tu red. Tus datos.
## Local. Solo lectura. Sin nube. Sin proxy.

> **Tu inversor TSUN puede funcionar ya**  
> No aparecer en la lista no significa que no sea compatible.

| Protocol | Hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Validado en hardware real |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ Validado en hardware real |
| **1097** | GEN3 family | 🧪 Experimental |

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

**Instala TSUN Local, deja que identifique el protocolo y comprueba qué datos expone tu inversor.**

## Diagnóstico avanzado

Los parámetros de red e inversor de solo lectura están desactivados por defecto y pueden activarse individualmente en Home Assistant.

- **1511:** grid protection diagnostics
- **02B0:** grid protection diagnostics + output coefficient
- **1097:** protocol/inverter versions, temperature, insulation impedance RX/RY, country/profile code and designed power

## Compatibilidad

### ✅ Validado en hardware real
- **TSOL-MP3000** — 1511 — 6 PV inputs
- **TSOL-MX500** — 02B0 — 1 PV input

### 🔎 Vale la pena probar
MP2250 · MS3000 · MX400 · MX450 · MX800 · MX900 · MX1000 · MX2250 · MS300 · MS350 · MS400 · MS600 · MS700 · MS800 · MS1600 · MS1800 · MS2000 and corresponding `-D` variants where applicable.

### 🧪 1097 — Experimental

¿Tienes otro modelo TSUN? Pruébalo: puede convertirse en el próximo dispositivo validado.

---

**Jean-Philippe TESTART (`jptstar`)** · Unofficial independent community project · GPL-3.0-or-later

El mapeo experimental 1097 se basa en la investigación pública de Stefan Allius / s-allius/tsun-gen3-proxy y se ha adaptado a TSUN Local.
