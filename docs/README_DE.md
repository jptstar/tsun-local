# TSUN Local 1.4.0

<p align="center">[English](../README.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [Nederlands](README_NL.md) · [Italiano](README_IT.md) · [Español](README_ES.md) · [Polski](README_PL.md) · [简体中文](README_ZH.md)</p>

### Dein Wechselrichter. Dein Netzwerk. Deine Daten.
## Lokal. Nur lesen. Keine Cloud. Kein Proxy.

> **Dein TSUN-Wechselrichter könnte bereits funktionieren**  
> Nicht aufgeführt bedeutet nicht automatisch nicht unterstützt.

| Protocol | Hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Auf echter Hardware validiert |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ Auf echter Hardware validiert |
| **1097** | GEN3 family | 🧪 Experimentell |

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

**Installiere TSUN Local, lasse das Protokoll erkennen und prüfe, welche Daten dein Wechselrichter bereitstellt.**

## Erweiterte Diagnose

Schreibgeschützte Netz- und Wechselrichterparameter sind standardmäßig deaktiviert und können in Home Assistant einzeln aktiviert werden.

- **1511:** grid protection diagnostics
- **02B0:** grid protection diagnostics + output coefficient
- **1097:** protocol/inverter versions, temperature, insulation impedance RX/RY, country/profile code and designed power

## Kompatibilität

### ✅ Auf echter Hardware validiert
- **TSOL-MP3000** — 1511 — 6 PV inputs
- **TSOL-MX500** — 02B0 — 1 PV input

### 🔎 Ausprobieren
MP2250 · MS3000 · MX400 · MX450 · MX800 · MX900 · MX1000 · MX2250 · MS300 · MS350 · MS400 · MS600 · MS700 · MS800 · MS1600 · MS1800 · MS2000 and corresponding `-D` variants where applicable.

### 🧪 1097 — Experimentell

Du hast ein anderes TSUN-Modell? Probiere es aus – es könnte das nächste validierte Gerät werden.

---

**Jean-Philippe TESTART (`jptstar`)** · Unofficial independent community project · GPL-3.0-or-later

Die experimentelle 1097-Zuordnung basiert auf öffentlich verfügbarer Forschung von Stefan Allius / s-allius/tsun-gen3-proxy und wurde für TSUN Local angepasst.
