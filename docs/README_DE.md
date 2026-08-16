<p align="center">
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/README.md">English</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_FR.md">Français</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_DE.md">Deutsch</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_NL.md">Nederlands</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_IT.md">Italiano</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_ES.md">Español</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_PL.md">Polski</a> ·
  <a href="https://github.com/jptstar/tsun-local/blob/beta-1097/docs/README_ZH.md">简体中文</a>
</p>

<p align="center">
  <img src="../custom_components/tsun_local/brand/icon@2x.png" width="160" alt="TSUN Local">
</p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Dein Wechselrichter. Dein Netzwerk. Deine Daten.</h3>
<p align="center"><strong>Lokal. Nur lesen. Keine Cloud. Kein Proxy.</strong></p>
<p align="center">Direkter lokaler Zugriff auf kompatible TSUN-Mikrowechselrichter in Home Assistant.<br><strong>1.4.0-beta.8</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

---

## Dein TSUN-Wechselrichter könnte bereits funktionieren

TSUN Local unterstützt **drei lokale TSUN-Protokollfamilien**.

| Protokoll | Familie / validierte Referenz | Status |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **Validiert** |
| **02B0** | GEN3 PLUS · **TSOL-MX500** | ✅ **Validiert** |
| **1097** | GEN3 | 🧪 **Experimentell** |

> [!TIP]
> **Nicht aufgeführt bedeutet nicht automatisch nicht unterstützt.** Wenn dein Wechselrichter **1511, 02B0 oder 1097** verwendet, könnte er bereits funktionieren.

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="TSUN Local zu HACS hinzufügen" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>Installieren. TSUN Local das Protokoll erkennen lassen. Prüfen, was dein Wechselrichter bereitstellt.</strong></p>

---

## Auf einen Blick

| | Was TSUN Local bereitstellt |
|---|---|
| ☀️ **PV** | Spannung · Strom · Leistung · Tagesenergie · Gesamtenergie |
| ⚡ **AC** | Spannung · Strom · Frequenz · Leistung · Tagesenergie · Gesamtenergie |
| 🚨 **Diagnose** | Alarme · Kommunikation · Logger-Informationen |
| 🛡️ **Erweitert** | Netzschutz · Wechselrichterdiagnose · Standardmäßig deaktiviert |
| 🔒 **Sicherheit** | Nur lesen · Keine Konfigurationsschreibzugriffe auf den Wechselrichter |

---

## Kompatibilität

**Home Assistant 2026.3.0 oder neuer.**

> [!NOTE]
> **✅ Validiert** = mit TSUN Local auf echter Hardware bestätigt.  
> **🔎 Wahrscheinlich kompatibel** = die Protokollfamilie wird unterstützt, dieses genaue Modell wurde mit TSUN Local aber noch nicht validiert.  
> **🧪 Experimentell** = Protokollunterstützung ist vorhanden, benötigt jedoch weitere Validierung auf realen Geräten.

### 1511 · TITAN — ✅ Validiert

**✅ Validiert**  
`TSOL-MP3000`

**🔎 Wahrscheinlich kompatibel**  
`TSOL-MP2250` · `TSOL-MS3000` *(TITAN-Generation)*

| | Verfügbare Daten |
|---|---|
| ☀️ **PV** | Bis zu 6 Eingänge · Spannung · Strom · Leistung · Tages- & Gesamtenergie |
| ⚡ **AC** | Spannung · Strom · Frequenz · Leistung · Tages- & Gesamtenergie |
| 🚨 **Diagnose** | Wechselrichteralarme |
| 🛡️ **Erweitert** | Netzschutz-Grenzwerte und Zeitdiagnosen |

### 02B0 · GEN3 PLUS — ✅ Validiert

**✅ Validiert**  
`TSOL-MX500`

**🔎 Wahrscheinlich kompatibel**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
Entsprechende `-D`-Varianten können ebenfalls kompatibel sein, sofern vorhanden.

> [!NOTE]
> Öffentliche GEN3-PLUS-Forschung ordnet diese Geräte im Allgemeinen der Seriennummernfamilie **Y17 / Y47** zu. Das hilft bei der Unterscheidung von Modellen, deren Namen auch bei älteren GEN3-Varianten vorkommen.

| | Verfügbare Daten |
|---|---|
| ☀️ **PV** | Dynamische PV-Eingangserkennung · Spannung · Strom · Leistung · Energie |
| ⚡ **AC** | Spannung · Strom · Frequenz · Leistung · Energie |
| 🚨 **Diagnose** | Wechselrichteralarme |
| 🛡️ **Erweitert** | Netzschutzdiagnose · Ausgangskoeffizient |

### 1097 · GEN3 — 🧪 Experimentell

**🔎 Wahrscheinlich kompatibel**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000`

> [!NOTE]
> Öffentliche GEN3-Forschung ordnet diese Geräte im Allgemeinen der Seriennummernfamilie **R17 / R47** zu. Die Kompatibilität mit dem TSUN-Local-Protokoll **1097** bleibt experimentell, bis sie auf mehr echter Hardware bestätigt wurde.

| | Verfügbare Daten |
|---|---|
| ☀️ **PV** | Standard-PV-Telemetrie |
| ⚡ **AC** | Standard-Wechselrichter-/AC-Telemetrie |
| 🚨 **Diagnose** | Verfügbare Wechselrichterdiagnosen |
| 🛡️ **Erweitert** | Protokollversion · Wechselrichterversion · Temperatur · Isolation RX/RY · Rohwert Land/Profil · Auslegungsleistung |

> **🔎 Wahrscheinlich kompatibel bedeutet nicht validiert.** Es bedeutet, dass TSUN Local die passende Protokollfamilie bereits implementiert und das Gerät damit ein guter Kompatibilitätskandidat ist.

---

## 🛡️ Erweiterte Diagnose

Erweiterte Entitäten sind absichtlich **standardmäßig deaktiviert**. Dadurch bleibt die normale Geräteseite übersichtlich, während technische Informationen bei Bedarf verfügbar bleiben.

Aktivierung:

**Einstellungen → Geräte & Dienste → TSUN Local → Gerät → Entitäten → Deaktivierte Entitäten**

Es sind keine Schreibzugriffe zur Konfiguration des Wechselrichters implementiert.

---

## Installation

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="TSUN Local zu HACS hinzufügen" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

Alternativ `https://github.com/jptstar/tsun-local` unter **HACS → Benutzerdefinierte Repositories → Integration** hinzufügen, **TSUN Local** installieren und Home Assistant neu starten.

### Manuell

`custom_components/tsun_local` nach `/config/custom_components/` kopieren, Home Assistant neu starten und anschließend **TSUN Local** unter **Einstellungen → Geräte & Dienste** hinzufügen.

---

## Funktionsweise

```text
TSUN-Wechselrichter
     │
     │ Lokales Netzwerk
     ▼
 TSUN Local
     │
     ▼
Home Assistant
```

**Keine Cloud im Datenpfad. Kein Proxy. Kein externer Laufzeitdienst. Keine Konfigurationsschreibzugriffe auf den Wechselrichter.**

Nur direkte lokale Abfrage.

---

## Ein anderes TSUN-Modell testen

Dein Wechselrichter muss nicht oben aufgeführt sein.

Wenn TSUN Local eines dieser Protokolle erkennt:

```text
1511
02B0
1097
```

lass die Integration laufen und prüfe die erkannten Entitäten.

> [!TIP]
> **Dein Wechselrichter könnte das nächste validierte Modell werden.** Hilfreich sind das genaue Modell, das erkannte Protokoll, die Anzahl der PV-Eingänge, die Firmwareversion und welche Entitäten plausible Werte liefern.

---

## TSUN Local 1.4

### Ein breiteres TSUN Local

Version 1.4 entwickelt TSUN Local von einzelnen bekannten Modellen hin zu **Kompatibilität auf Protokollfamilien-Ebene**.

| | |
|---|---|
| 🔌 | **1511 · 02B0 · 1097** |
| 🔍 | Automatische Protokollerkennung |
| ☀️ | Progressive / dynamische PV-Eingangserkennung |
| 📊 | Erweiterte lokale Telemetrie |
| 🛡️ | Erweiterte Nur-Lese-Diagnose |
| 🌍 | 8 Sprachen |
| 🧪 | Einfacheres Testen neuer TSUN-Modelle |

---

## Reverse Engineering & Validierung

Die Implementierungen 1511 und 02B0 entstehen durch **unabhängige lokale Protokollanalyse, Beobachtungen an realen Geräten und Hardwarevalidierung**.

Die experimentelle 1097-Zuordnung wurde durch öffentlich verfügbare Protokollforschung von **Stefan Allius / `s-allius/tsun-gen3-proxy`** unterstützt und anschließend für den direkten lokalen Einsatz in TSUN Local angepasst.

Kompatibilitätskandidaten werden bewusst getrennt von tatsächlich validierter Hardware gekennzeichnet.

---

## Projekt

> [!IMPORTANT]
> **Inoffizielles Community-Projekt.** TSUN Local ist unabhängig und wird weder von TSUN entwickelt, genehmigt, unterstützt noch gepflegt.

Erstellt und gepflegt von **Jean-Philippe TESTART · `jptstar`**  
*Aus Spaß, technischer Neugier und für die Home-Assistant-Community entwickelt und geteilt.*

---

## Lizenz

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Veröffentlicht unter der **GNU General Public License v3.0 oder später**. Siehe [LICENSE](../LICENSE).
