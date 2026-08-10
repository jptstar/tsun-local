# TSUN Local — Lokale Home-Assistant-Integration

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Unabhängiges TSUN-Local-Symbol">
</p>

> **Inoffizielles Projekt** — Diese unabhängige Community-Integration wird weder von TSUN entwickelt noch genehmigt oder gewartet und steht in keiner Verbindung zu TSUN. TSUN und seine Produktnamen bleiben Eigentum der jeweiligen Rechteinhaber. Supportanfragen zu dieser Integration sind an den Autor und nicht an TSUN zu richten.

Unabhängige Implementierung des lokalen 1511-Protokolls, das von ausgewählten TSUN-Mikrowechselrichtern verwendet wird. Sie kommuniziert im lokalen Netzwerk direkt mit dem Logger und benötigt keinen Cloud-Dienst.

**TSUN Local ist die Softwarebasis des Projekts.** Die allgemeine Home-Assistant-Domain `tsun_local` soll stabil bleiben, während Unterstützung für weitere Modelle und lokale Protokolle ergänzt wird. Version 1.0.0 enthält die erste validierte Implementierung für den TSOL-MP3000 mit Protokoll 1511.

Die Architektur trennt den Home-Assistant-Koordinator und die Entitäten von den Protokolladaptern in `custom_components/tsun_local/protocols/`. Jeder Adapter deklariert seine eigenen Messwerte, damit Home Assistant nur unterstützte Entitäten erstellt. `protocol_1511.py` ist der erste Adapter; zukünftige TSUN-Protokolle können in diesem Verzeichnis ergänzt werden, ohne die Integration umzubenennen.

**Autor: Jean-Philippe TESTART (jptstar)**

## Lizenz

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Dieses Projekt wird unter der **GNU General Public License v3.0 oder höher** (`GPL-3.0-or-later`) veröffentlicht. Geänderte oder weiterverteilte Versionen müssen die Lizenzbedingungen einhalten und die Copyright- und Lizenzhinweise beibehalten. Siehe [LICENSE](LICENSE).

Die Lizenz gilt ausschließlich für diese unabhängige Implementierung. Sie gewährt keine Rechte an Marken, Logos, Software oder Produkten von TSUN. Dieses Projekt bleibt inoffiziell und unabhängig von TSUN.

## Versionen

Veröffentlichte Versionen folgen `MAJOR.MINOR.PATCH`. HACS verwendet GitHub Releases, um Aktualisierungen anzubieten. Einzelheiten stehen im [Änderungsprotokoll](CHANGELOG.md).

## Kompatibilität

- **Home Assistant 2026.3.0 oder neuer**.
- **TSOL-MP3000**: kompatibel und auf echter Hardware mit 6 PV-Eingängen validiert.
- **TSOL-MP2250**: für eine spätere Validierung vorgesehen; Unterstützung wird erst nach Bestätigung auf echter Hardware angekündigt.

## Installation

### Mit HACS

1. Öffne in HACS **Integrationen** und anschließend **Benutzerdefinierte Repositories**.
2. Füge `https://github.com/jptstar/tsun-local` mit dem Typ **Integration** hinzu.
3. Installiere **TSUN Local** und starte Home Assistant neu.

### Manuelle Installation

1. Kopiere `custom_components/tsun_local` nach `/config/custom_components/`.
2. Starte Home Assistant neu.
3. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
4. Suche nach **TSUN Local**.
5. Gib IP-Adresse, Port und die **SN auf dem Typenschild des Mikrowechselrichters** ein.

## Mehrere Geräte

Mehrere kompatible Mikrowechselrichter können derselben Home-Assistant-Installation hinzugefügt werden. Führe für jedes Gerät **Integration hinzufügen** aus und gib seine IP-Adresse und eindeutige SN ein. Jeder Eintrag erstellt ein unabhängiges Gerät mit eigenen Entitäten und eigenem Kommunikationskoordinator.

## Einstellungen in Home Assistant

Öffne unter **Einstellungen → Geräte & Dienste → TSUN Local** das Menü des betreffenden Geräts:

- **Konfigurieren** legt das normale Intervall zwischen 10 Sekunden und 5 Minuten (standardmäßig 30 Sekunden) sowie das Offline-/Nachtintervall zwischen 1 und 60 Minuten (standardmäßig 5 Minuten) fest;
- **Neu konfigurieren** ändert IP-Adresse und TCP-Port, ohne Entitäten zu löschen;
- jedes Gerät besitzt unabhängige Abfrageintervalle.

## Nachtbetrieb

Wenn der Mikrowechselrichter nicht mehr mit Strom versorgt wird, markiert ihn die Integration als offline, ohne bei jeder Abfrage erneut einen Fehler zu melden:

- AC-/PV-Messwerte werden nicht verfügbar, damit keine veralteten Werte angezeigt werden;
- die Diagnose **Kommunikation** meldet offline;
- der Zähler aufeinanderfolgender Fehler wird nach Wiederherstellung der Kommunikation auf null gesetzt;
- der Zeitpunkt der letzten erfolgreichen Kommunikation bleibt verfügbar;
- Wiederholungsversuche verwenden das konfigurierte Offline-/Nachtintervall;
- nach der ersten erfolgreichen Antwort am Morgen wird das normale Intervall wiederhergestellt.

## Sensoren

Die Integration erstellt ein Gerät mit AC-Messwerten, 5 Messwerten für jeden der 6 PV-Eingänge, der Summe der 6 DC-Leistungen, 4 Diagnosesensoren und einem Verbindungsstatus.

Die drei Protokollblöcke sind `01/0x0BB8–0x0BD0`, `03/0x0E10–0x0E2D` und `04/0x0ED8–0x0EF5`.
