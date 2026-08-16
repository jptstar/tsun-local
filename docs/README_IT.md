# TSUN Local 1.4.0

<p align="center">[English](../README.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [Nederlands](README_NL.md) · [Italiano](README_IT.md) · [Español](README_ES.md) · [Polski](README_PL.md) · [简体中文](README_ZH.md)</p>

### Il tuo inverter. La tua rete. I tuoi dati.
## Locale. Sola lettura. Nessun cloud. Nessun proxy.

> **Il tuo inverter TSUN potrebbe già funzionare**  
> Non presente nell’elenco non significa non supportato.

| Protocol | Hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Validato su hardware reale |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ Validato su hardware reale |
| **1097** | GEN3 family | 🧪 Sperimentale |

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

**Installa TSUN Local, lascia che identifichi il protocollo e verifica i dati esposti dall’inverter.**

## Diagnostica avanzata

I parametri di rete e inverter in sola lettura sono disattivati per impostazione predefinita e possono essere attivati singolarmente in Home Assistant.

- **1511:** grid protection diagnostics
- **02B0:** grid protection diagnostics + output coefficient
- **1097:** protocol/inverter versions, temperature, insulation impedance RX/RY, country/profile code and designed power

## Compatibilità

### ✅ Validato su hardware reale
- **TSOL-MP3000** — 1511 — 6 PV inputs
- **TSOL-MX500** — 02B0 — 1 PV input

### 🔎 Da provare
MP2250 · MS3000 · MX400 · MX450 · MX800 · MX900 · MX1000 · MX2250 · MS300 · MS350 · MS400 · MS600 · MS700 · MS800 · MS1600 · MS1800 · MS2000 and corresponding `-D` variants where applicable.

### 🧪 1097 — Sperimentale

Hai un altro modello TSUN? Provalo: potrebbe diventare il prossimo dispositivo validato.

---

**Jean-Philippe TESTART (`jptstar`)** · Unofficial independent community project · GPL-3.0-or-later

La mappatura sperimentale 1097 si basa sulla ricerca pubblica di Stefan Allius / s-allius/tsun-gen3-proxy ed è stata adattata a TSUN Local.
