# TSUN Local 1.4.0

<p align="center">[English](../README.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [Nederlands](README_NL.md) · [Italiano](README_IT.md) · [Español](README_ES.md) · [Polski](README_PL.md) · [简体中文](README_ZH.md)</p>

### Twój falownik. Twoja sieć. Twoje dane.
## Lokalnie. Tylko odczyt. Bez chmury. Bez proxy.

> **Twój falownik TSUN może już działać**  
> Brak modelu na liście nie oznacza braku obsługi.

| Protocol | Hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Zweryfikowano na rzeczywistym sprzęcie |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ Zweryfikowano na rzeczywistym sprzęcie |
| **1097** | GEN3 family | 🧪 Eksperymentalne |

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

**Zainstaluj TSUN Local, pozwól wykryć protokół i sprawdź dane udostępniane przez falownik.**

## Zaawansowana diagnostyka

Parametry sieci i falownika tylko do odczytu są domyślnie wyłączone i można je włączać pojedynczo w Home Assistant.

- **1511:** grid protection diagnostics
- **02B0:** grid protection diagnostics + output coefficient
- **1097:** protocol/inverter versions, temperature, insulation impedance RX/RY, country/profile code and designed power

## Kompatybilność

### ✅ Zweryfikowano na rzeczywistym sprzęcie
- **TSOL-MP3000** — 1511 — 6 PV inputs
- **TSOL-MX500** — 02B0 — 1 PV input

### 🔎 Warto wypróbować
MP2250 · MS3000 · MX400 · MX450 · MX800 · MX900 · MX1000 · MX2250 · MS300 · MS350 · MS400 · MS600 · MS700 · MS800 · MS1600 · MS1800 · MS2000 and corresponding `-D` variants where applicable.

### 🧪 1097 — Eksperymentalne

Masz inny model TSUN? Wypróbuj go — może zostać kolejnym zweryfikowanym urządzeniem.

---

**Jean-Philippe TESTART (`jptstar`)** · Unofficial independent community project · GPL-3.0-or-later

Eksperymentalna mapa 1097 korzysta z publicznych badań Stefana Alliusa / s-allius/tsun-gen3-proxy i została dostosowana do TSUN Local.
