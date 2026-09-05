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
  <img src="../custom_components/tsun_local/brand/icon@2x.png" width="160" alt="TSUN Local">
</p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Dein Wechselrichter. Dein Netzwerk. Deine Daten.</h3>
<p align="center"><strong>Lokal. Nur lesen. Keine Cloud. Kein Proxy.</strong></p>
<p align="center">Direkter lokaler Zugriff auf kompatible TSUN-Mikrowechselrichter in Home Assistant.<br><strong>1.6.0</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>


---

## Kompatibilität

**Home Assistant 2026.3.0 oder neuer.**

| Protokoll | Familie | Validierte Hardware | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validiert** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2** | ✅ **Validiert** |
| **1097** | GEN3 / GEN3 PLUS | — | 🧪 **Experimentell** |

> [!TIP]
> **Nicht aufgeführt bedeutet nicht inkompatibel.** TSUN Local bewertet die Kompatibilität in erster Linie anhand des erkannten lokalen Protokolls und nicht nur anhand des Modellnamens.

<details>
<summary><strong>Voraussichtlich kompatible Modelle nach Protokoll</strong></summary>

- **1511 — Voraussichtlich kompatibel:** `TSOL-MP2250` · `TSOL-MS3000` (TITAN)
- **02B0 — Voraussichtlich kompatibel:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800` · entsprechende `-D`-Varianten
- **1097 — Voraussichtlich kompatibel:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

</details>

📚 **[MP3000 / TITAN Validierung](MP3000_FIELD_VALIDATION.md)**

📚 **[TSOL-MX500 Home Assistant](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html)** · **[TSOL-MS800 Home Assistant](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html)** · **[TSOL-MS2000 Home Assistant](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html)**

**Neu in 1.6.0:** Der **adaptive Abruf** ist standardmäßig aktiviert und passt das Abfrageintervall bei Kommunikationsfehlern automatisch an: 20 s normal, 30 s nach einem Fehler und 300 s offline/Nacht.

📚 **[Vollständige Entitätsreferenz](ENTITIES.md)**

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="TSUN Local zu HACS hinzufügen" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

---


## Auf einen Blick

| | Was TSUN Local bereitstellt |
|---|---|
| ☀️ **PV** | Spannung · Strom · Leistung · Tagesenergie · Gesamtenergie |
| ⚡ **AC** | Spannung · Strom · Frequenz · Leistung · Tagesenergie · Gesamtenergie |
| 🚨 **Diagnose** | Aktive Alarme · Kommunikation · Logger-Informationen |
| 🛡️ **Erweitert** | Netzschutz · Firmware · Wechselrichterdiagnose · Experimentelle Feldvalidierungsdaten |
| 🔒 **Sicherheit** | Nur lesen · Keine Konfigurationsschreibzugriffe auf den Wechselrichter |

📚 **[Vollständige Entitätsreferenz nach Protokoll](ENTITIES.md)**


---


## 🚨 MP3000-Alarme

TSUN Local unterstützt das vollständige MP3000-Alarmbitfeld und hält die Home-Assistant-Oberfläche trotzdem kompakt. **Alle 224 Alarmpositionen werden erhalten und ausgewertet, wenn sie aktiv werden.**

Die **12 auf Hardware beobachteten funktionalen Zuordnungen** umfassen niedrige PV-Eingangsspannung und PV-DSP-Fehler für PV1 bis PV6. Die übrigen **212 Positionen** behalten stabile neutrale TSUN-Local-Kennungen, bis ihre funktionale Bedeutung physisch validiert ist.

Home Assistant zeigt einen **Wechselrichteralarm**, die Anzahl **Aktiver Alarme** und einen Sensor **Namen aktiver Alarme**. Die 14 vollständigen Rohwörter bleiben als standardmäßig deaktivierte Diagnose verfügbar, ohne 224 permanente Entitäten anzulegen.


---


> [!TIP]
> Aktive Alarme werden außerdem als **lokalisierter Klartext** mit stabilem Positionscode angezeigt, zum Beispiel `Grid undervoltage (02B0-A014)` in der jeweiligen Home-Assistant-Sprache. **Sunology PLAY2** nutzt dieselbe kompakte 02B0-Alarmoberfläche; die vier rohen ERR-Wörter bleiben als erweiterte Diagnose verfügbar.

## 🛡️ Erweiterte Diagnose

Erweiterte Entitäten sind absichtlich **standardmäßig deaktiviert**. Dazu gehören je nach Protokoll Netzschutzwerte, Firmware- und Wechselrichterdiagnosen sowie ausgewählte experimentelle Feldvalidierungswerte.

Aktivierung:

**Einstellungen → Geräte & Dienste → TSUN Local → Gerät → Entitäten → Deaktivierte Entitäten**

Experimentelle semantische Zuordnungen bleiben bis zur unabhängigen Validierung ausdrücklich gekennzeichnet. Es sind keine Konfigurationsschreibzugriffe auf den Wechselrichter implementiert.

📚 **[MP3000 Feldvalidierungsnachweise](MP3000_FIELD_VALIDATION.md)**
📚 **[Vollständige Entitätsreferenz](ENTITIES.md)**


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


## 🔬 Ein anderes TSUN-Modell validieren

TSUN Local bietet eine datenschutzfreundliche, **streng schreibgeschützte** Hardware-Diagnose für nicht aufgeführte Modelle und Kommunikationsprobleme.

### Windows — einfachste Variante

**⬇️ [`TSUN-Local-Diagnostic.exe` herunterladen](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)**

Keine Installation und keine Python-Umgebung erforderlich. Die portable Anwendung verwendet dieselbe schreibgeschützte Diagnose-Engine, erkennt TSUN-Logger, prüft die Protokolle **1511 / 02B0 / 1097** und erstellt einen anonymisierten JSON-Bericht.

Bei Kommunikationsproblemen oder nicht verfügbaren Entitäten **den betroffenen TSUN-Local-Konfigurationseintrag vor der Erfassung deaktivieren** und danach wieder aktivieren.

### macOS / Linux / fortgeschrittene Benutzer

**⬇️ [`tsun_dump.py` herunterladen](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)** — Python 3.10+.

```bash
python3 tsun_dump.py --full
```

Unter Windows kann das Skript weiterhin mit `py tsun_dump.py --full` verwendet werden.

📚 **[Hardware Validation Dump Tool Leitfaden](HARDWARE_DUMP.md)**

### Sunology PLAY2

**Sunology PLAY2 wurde auf echter Home-Assistant-Hardware validiert** – über den lokalen 02B0-/Solarman-V5-Pfad.

- Automatische Erkennung und normaler TSUN-Local-Einrichtungsablauf wurden unabhängig bestätigt.
- Lokal und schreibgeschützt: keine Cloud und keine Konfigurationsschreibvorgänge zum Wechselrichter.
- Die genaue MX400/MX450/MX500-Hardwarevariante bleibt bewusst offen; maßgeblich ist das erkannte **02B0**-Protokoll.

📚 **[PLAY2-Forschungsdetails](PLAY2_LOCAL_RESEARCH.md)** · 🔬 **[Optionaler schreibgeschützter PLAY2-Test](../tools/tsun_play2_probe.py)**

---


## Einen nicht aufgeführten Wechselrichter testen

Wenn TSUN Local `1511`, `02B0` oder `1097` erkennt, lass die Integration laufen und prüfe die entdeckten Entitäten.

Hilfreiches Feedback umfasst das genaue Modell, das erkannte Protokoll, die Firmwareversion, die Anzahl der PV-Eingänge und welche Entitäten plausible Werte liefern.

> [!TIP]
> **Dein Wechselrichter könnte das nächste validierte Modell werden.**


---


## Validierungsrichtlinie

TSUN Local trennt bestätigte Hardwareunterstützung von experimenteller Protokollforschung.

Funktionsnamen und Modellunterstützung werden erst nach reproduzierbaren Prüfungen auf echter Hardware als validiert gekennzeichnet. Ein Wert, der lediglich zu einem erwarteten Profil passt, gilt als Hinweis und nicht als Beweis; experimentelle Zuordnungen bleiben gekennzeichnet, bis eine unabhängige Beobachtung sie eindeutig unterscheidet.


---

## Beiträge und Credits

TSUN Local profitiert von öffentlicher Protokollforschung und unabhängigen Hardwaretests. Die Nennung beschreibt Referenzarbeit und Validierung und bedeutet keine Zugehörigkeit oder Empfehlung.

- **David Rapan / [`ha-solarman`](https://github.com/davidrapan/ha-solarman)** — unabhängige öffentliche Referenz für ausgewählte Solarman-/02B0-Register.
- **Stefan Allius / [`tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy)** — öffentliche GEN3-/1097- und Länder-/Profilforschung für experimentelle Validierung.
- **TheSmartGerman** — Realgerätetest, durch den die zusätzliche 1097-Protokollfamilie sichtbar wurde.
- **dca31** — unabhängige Sunology-PLAY2-Validierung über den normalen TSUN-Local-Home-Assistant-Ablauf.
- **Kmotr** — unabhängige TSOL-MS800-Validierung mit TSUN Local und einem anonymisierten Home-Assistant-Diagnosebericht.
- **paloindici** — unabhängige TSOL-MS2000-Validierung mit TSUN Local, einschließlich anonymisierter Home-Assistant-Diagnosen für TSOL-MS2000 und TSOL-MP3000 sowie eines Hardware-Dumps zur Bestätigung des 02B0-/Vier-PV-Pfads.

📚 **[Alle Mitwirkenden und Credits](contributors.html)**

---


## Projekt

> [!IMPORTANT]
> **Inoffizielles Community-Projekt.** TSUN Local ist unabhängig und wird weder von TSUN entwickelt, genehmigt, unterstützt noch gewartet.

Erstellt und gepflegt von **Jean-Philippe TESTART · `jptstar`**
*Entwickelt und geteilt aus Spaß, technischer Neugier und für die Home-Assistant-Community.*


---


## Lizenz

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

Veröffentlicht unter **GNU General Public License v3.0 oder neuer**. Siehe [LICENSE](../LICENSE).
