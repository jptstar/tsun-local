# TSUN Local — Lokale Home-Assistant-Integration

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Unabhängiges TSUN-Local-Symbol">
</p>

> **Inoffizielles Projekt** — Diese unabhängige Community-Integration wird weder von TSUN entwickelt noch genehmigt oder gewartet und steht in keiner Verbindung zu TSUN. TSUN und seine Produktnamen bleiben Eigentum der jeweiligen Rechteinhaber. Supportanfragen zu dieser Integration sind an den Autor und nicht an TSUN zu richten.

**TSUN Local** bindet kompatible TSUN-Mikrowechselrichter über das lokale Netzwerk direkt in Home Assistant ein, ohne Proxy oder Cloud-Dienst. Version 1.1.4 unterstützt die auf echter Hardware validierten Modelle **TSOL-MP3000** und **MX500** sowie weitere **TITAN**-, **GEN3**- und **GEN3 PLUS**-Modelle, deren Validierung noch aussteht.

**Autor: Jean-Philippe TESTART (jptstar)**

## Lizenz

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Dieses Projekt wird unter der **GNU General Public License v3.0 oder höher** (`GPL-3.0-or-later`) veröffentlicht. Geänderte oder weiterverteilte Versionen müssen die Lizenzbedingungen einhalten und die Copyright- und Lizenzhinweise beibehalten. Siehe [LICENSE](LICENSE).

Die Lizenz gilt ausschließlich für diese unabhängige Implementierung. Sie gewährt keine Rechte an Marken, Logos, Software oder Produkten von TSUN. Dieses Projekt bleibt inoffiziell und unabhängig von TSUN.

## Versionen

Veröffentlichte Versionen folgen `MAJOR.MINOR.PATCH`. HACS verwendet GitHub Releases, um Aktualisierungen anzubieten. Einzelheiten stehen im [Änderungsprotokoll](CHANGELOG.md).

## Kompatibilität

**Home Assistant 2026.3.0 oder neuer**

### Legende

- ✅ Kompatibel und auf echter Hardware validiert
- ❌ Adapter verfügbar, Hardwarevalidierung ausstehend
- ⛔ Derzeit nicht unterstützt

### Mikrowechselrichter

| Familie | Modelle | Status |
|---|---|---|
| TITAN 2250 W–3000 W | **TSOL-MP3000** | ✅ Validiert |
| TITAN 2250 W–3000 W | **TSOL-MP2250, TSOL-MS3000** | ❌ Validierung ausstehend |
| TITAN 3680 W–6000 W | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | ⛔ Nicht unterstützt |
| GEN3 / GEN3 PLUS | **MS300, MS350, MS400, MS400-D** | ❌ Validierung ausstehend |
| GEN3 / GEN3 PLUS | **MS600, MS700, MS800, MS600-D, MS800-D** | ❌ Validierung ausstehend |
| GEN3 / GEN3 PLUS | **MS1600, MS1800, MS2000, MS2000-D** | ❌ Validierung ausstehend |
| GEN3 / GEN3 PLUS | **MS3000** | ❌ Validierung ausstehend |
| GEN3 / GEN3 PLUS | **MX500** | ✅ Validiert |
| GEN3 / GEN3 PLUS | **MX450, MX1000** | ❌ Validierung ausstehend |
| GEN3 / GEN3 PLUS | **MX3000** | ⛔ Nicht unterstützt |

Der GEN3-/GEN3-PLUS-Adapter erkennt Geräte mit **1, 2 oder 4 PV-Eingängen** dynamisch.

Der **MX3000** wird nicht unterstützt, da die verfügbare Karte bei PV4 endet, während dieses Modell zusätzliche Eingänge haben kann.

### Andere Geräte

| Typ | Modelle | Status |
|---|---|---|
| Speichersystem | **DC1000** | ⛔ Nicht unterstützt |
| Smart Meter | **TSOL-MG3-MS, DDZY422-D2** | ⛔ Nicht unterstützt |

## Installation

### Mit HACS

[![TSUN Local zu HACS hinzufügen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Oder manuell hinzufügen:

1. Öffne in HACS das Menü **⋮** oben rechts und wähle **Benutzerdefinierte Repositories**.
2. Füge `https://github.com/jptstar/tsun-local` mit dem Typ **Integration** hinzu.
3. Wähle **Hinzufügen** und öffne anschließend **TSUN Local**.
4. Wähle **Herunterladen** und die neueste verfügbare Version.
5. Starte Home Assistant neu.

Wenn die neueste Version nicht angezeigt wird, öffne das Repository-Menü und wähle **Informationen aktualisieren**.

### Manuelle Installation

1. Kopiere `custom_components/tsun_local` nach `/config/custom_components/`.
2. Starte Home Assistant neu.
3. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
4. Suche nach **TSUN Local**.
5. Gib IP-Adresse, Port und die **SN auf dem Typenschild des Mikrowechselrichters** ein.

Wähle beim Hinzufügen **Lokales Netzwerk durchsuchen** oder **Manuelle Konfiguration** und anschließend **TITAN** für den TSOL-MP3000 beziehungsweise **GEN3 / GEN3 PLUS** für den MX500. Gib die auf dem Typenschild angegebene **Monitor SN / Logger SN** ein. Die Suche prüft nur das lokale IPv4-Netz auf Port 8899 und sendet keine Daten an mögliche Geräteadressen.

## Mehrere Geräte

Mehrere kompatible Mikrowechselrichter können derselben Home-Assistant-Installation hinzugefügt werden. Führe für jedes Gerät **Integration hinzufügen** aus und gib seine IP-Adresse und eindeutige SN ein. Jeder Eintrag erstellt ein unabhängiges Gerät mit eigenen Entitäten und eigenem Kommunikationskoordinator.

## Einstellungen in Home Assistant

Öffne unter **Einstellungen → Geräte & Dienste → TSUN Local** das Menü des betreffenden Geräts:

- **Konfigurieren** legt das normale Intervall zwischen 10 Sekunden und 5 Minuten (standardmäßig 30 Sekunden) sowie das Offline-/Nachtintervall zwischen 1 und 60 Minuten (standardmäßig 5 Minuten) fest;
- **Neu konfigurieren** ändert IP-Adresse und TCP-Port, ohne Entitäten zu löschen;
- jedes Gerät besitzt unabhängige Abfrageintervalle.

## Lokaler Betrieb und Cloud-Isolierung

TSUN Local kommuniziert ausschließlich im lokalen Netzwerk und verwendet keinen Cloud-Dienst. Die Integration ändert jedoch keine Cloud-Einstellungen der Gerätefirmware.

Um den Internetzugriff des Mikrowechselrichters zu sperren, erstelle im Router oder in der Firewall eine Regel, die den WAN-Zugriff blockiert, aber lokales Netzwerk und DHCP erlaubt. Home Assistant muss die IP-Adresse des Mikrowechselrichters weiterhin über TCP-Port **8899** erreichen dürfen. Nach der Installation benötigt HACS Internet nur zum Prüfen und Herunterladen von Aktualisierungen.

## Nachtbetrieb

Wenn der Mikrowechselrichter nicht mehr mit Strom versorgt wird, markiert ihn die Integration als offline, ohne bei jeder Abfrage erneut einen Fehler zu melden:

- Momentanwerte (Spannung, Strom, Leistung und Frequenz) werden nicht verfügbar, damit keine veralteten Werte angezeigt werden;
- tägliche und gesamte Energiezähler bleiben mit ihrem letzten bekannten Wert verfügbar;
- die Diagnose **Kommunikation** meldet offline;
- der Zähler aufeinanderfolgender Fehler wird nach Wiederherstellung der Kommunikation auf null gesetzt;
- der Zeitpunkt der letzten erfolgreichen Kommunikation bleibt verfügbar;
- Wiederholungsversuche verwenden das konfigurierte Offline-/Nachtintervall;
- nach der ersten erfolgreichen Antwort am Morgen wird das normale Intervall wiederhergestellt.

## Sensoren

Die Integration erstellt ein Gerät mit AC-Messwerten, 5 Messwerten für jeden erkannten PV-Eingang, der Summe der erkannten DC-Leistungen, 4 Diagnosesensoren und einem Verbindungsstatus.

Die Anzahl der PV-Eingänge wird dynamisch ermittelt: PV1 ist nach der ersten Abfrage verfügbar; PV2 bis PV6 bei TITAN beziehungsweise PV2 bis PV4 bei GEN3/GEN3 PLUS werden hinzugefügt, sobald ein gültiger Messwert oder Energiezähler erkannt wird. Ein erkannter Eingang bleibt in Home Assistant registriert.
