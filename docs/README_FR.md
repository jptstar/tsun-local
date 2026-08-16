# TSUN Local 1.4.0

<p align="center">[English](../README.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [Nederlands](README_NL.md) · [Italiano](README_IT.md) · [Español](README_ES.md) · [Polski](README_PL.md) · [简体中文](README_ZH.md)</p>

### Votre onduleur. Votre réseau. Vos données.
## Local. Lecture seule. Sans cloud. Sans proxy.

> **Votre micro-onduleur TSUN fonctionne peut-être déjà**  
> Un modèle non listé n’est pas forcément incompatible.

| Protocol | Hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Validé sur matériel réel |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ Validé sur matériel réel |
| **1097** | GEN3 family | 🧪 Expérimental |

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

**Installez TSUN Local, laissez l’intégration identifier le protocole et voyez les données exposées.**

## Diagnostics avancés

Les paramètres réseau et onduleur en lecture seule sont désactivés par défaut et peuvent être activés individuellement dans Home Assistant.

- **1511:** grid protection diagnostics
- **02B0:** grid protection diagnostics + output coefficient
- **1097:** protocol/inverter versions, temperature, insulation impedance RX/RY, country/profile code and designed power

## Compatibilité

### ✅ Validé sur matériel réel
- **TSOL-MP3000** — 1511 — 6 PV inputs
- **TSOL-MX500** — 02B0 — 1 PV input

### 🔎 À tester
MP2250 · MS3000 · MX400 · MX450 · MX800 · MX900 · MX1000 · MX2250 · MS300 · MS350 · MS400 · MS600 · MS700 · MS800 · MS1600 · MS1800 · MS2000 and corresponding `-D` variants where applicable.

### 🧪 1097 — Expérimental

Vous possédez un autre modèle TSUN ? Essayez-le : il peut devenir le prochain modèle validé.

---

**Jean-Philippe TESTART (`jptstar`)** · Unofficial independent community project · GPL-3.0-or-later

Le mapping expérimental 1097 s’appuie sur les recherches publiques de Stefan Allius / s-allius/tsun-gen3-proxy et a été adapté à TSUN Local.
