# TSUN Local — Lokale Home-Assistant-Integration

[English](../README.md) | [Français](README_FR.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub-Version](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Unabhängiges TSUN-Local-Symbol">
</p>

> **Inoffizielles Projekt** — Diese unabhängige Community-Integration wird weder von TSUN entwickelt noch genehmigt oder gewartet und steht in keiner Verbindung zu TSUN. TSUN und seine Produktnamen bleiben Eigentum der jeweiligen Rechteinhaber. Supportanfragen zu dieser Integration sind an den Autor und nicht an TSUN zu richten.

**TSUN Local** verbindet kompatible TSUN-Mikrowechselrichter über das lokale Netzwerk direkt mit Home Assistant, ohne Proxy oder Cloud-Dienst. Version **1.3.0** unterstützt die auf echter Hardware geprüften Modelle **TSOL-MP3000** und **TSOL-MX500** und stellt testbereite Adapter für weitere TITAN-, GEN3- und GEN3-PLUS-Modelle bereit.

## Über dieses Projekt

Ich habe diese Integration ursprünglich aus Freude an der Technik und für meine eigene Home-Assistant-Installation entwickelt. Da viele Besitzer Schwierigkeiten mit dem lokalen Zugriff auf ihre TSUN-Mikrowechselrichter haben, stelle ich sie auch anderen zur Verfügung.

Hardware-Rückmeldungen, Diagnoseergebnisse und präzise Fehlerberichte sind willkommen. Wenn verwertbare Informationen vorliegen, kann ich etwas Zeit in weitere Verbesserungen investieren. Das Projekt bleibt jedoch ein persönliches Hobby und ist nicht meine Haupttätigkeit; Antworten und Korrekturen können daher manchmal etwas länger dauern.

## Hauptfunktionen

- vollständig lokale TCP-Abfrage ohne Proxy und ohne Cloud-Abhängigkeit;
- automatische Auswahl des unterstützten lokalen Protokolladapters;
- automatische Erkennung der verfügbaren PV-Eingänge innerhalb der validierten Registerkarten;
- AC-Spannung, Strom, Frequenz, Leistung sowie Tages- und Gesamtenergie;
- Spannung, Strom, Leistung sowie Tages- und Gesamtenergie je erkanntem PV-Eingang;
- berechnete DC-Gesamtleistung aus den erkannten PV-Leistungen;
- rohe Wechselrichteralarme und globaler Alarmstatus;
- Kommunikationsdiagnosen mit getrennten Intervallen für Normalbetrieb, Fehlerwiederholung und Offline/Nacht;
- eine Schaltfläche je Gerät zum sofortigen manuellen Aktualisieren der Daten;
- mehrere Mikrowechselrichter in einer Home-Assistant-Installation;
- übersetzte Home-Assistant-Entitäten auf Deutsch, Englisch, Französisch, Spanisch, Italienisch, Niederländisch, Polnisch und vereinfachtem Chinesisch.

## Kompatibilität

- **Home Assistant 2026.3.0 oder neuer**.

**Legende:** ✅ auf echter Hardware validiert · 🧪 Adapter bereit für Community-Tests · 🔎 zusätzliche Registerinformationen oder Hardware-Aufzeichnungen erforderlich · ⏸️ derzeit nicht im Projektumfang.

### TITAN-Mikrowechselrichter

| PV-Eingänge | Modelle | Status | Hinweise |
|---:|---|:---:|---|
| 6 | **TSOL-MP3000** | ✅ | Auf echter Hardware validiert |
| 6 | TSOL-MP2250, TSOL-MS3000 | 🧪 | 1511-Adapter ist testbereit |
| 6 | MP3680, MP3750, MP4000, MP4600, MP5000, MP6000 | 🔎 | Hardware mit sechs Eingängen; lokales Protokoll und Registerkarte müssen noch durch einen Hardware-Mitschnitt bestätigt werden |

### GEN3- und GEN3-PLUS-Mikrowechselrichter

| PV-Eingänge | Modelle | Status | Hinweise |
|---:|---|:---:|---|
| 1 | **TSOL-MX500** | ✅ | Auf echter Hardware validiert |
| 1 | MX400, MX450, MS300, MS350, MS400, MS400-D | 🧪 | 02B0-Adapter ist testbereit |
| 2 | MX800, MX900, MX1000, MS600, MS700, MS800, MS600-D, MS700-D, MS800-D | 🧪 | 02B0-Adapter ist testbereit |
| 4 | MX2250, MS1600, MS1800, MS2000, MS2000-D | 🧪 | 02B0-Adapter ist testbereit |
| 6 | MS3000, MX2400, MX2500, MX2700, MX3000/MX3000D, MX3300 | 🔎 | Die verfügbare 02B0-Karte endet derzeit bei PV4 |

## Installation

### Mit HACS

[![TSUN Local zu HACS hinzufügen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Oder manuell hinzufügen:

1. Öffne in HACS das Menü **⋮** und wähle **Benutzerdefinierte Repositories**.
2. Füge `https://github.com/jptstar/tsun-local` mit dem Typ **Integration** hinzu.
3. Öffne **TSUN Local**, wähle **Herunterladen** und anschließend die neueste Version.
4. Starte Home Assistant neu.

Wenn eine neue Version nicht erscheint, öffne das Repository-Menü und wähle **Informationen aktualisieren**.

### Manuelle Installation

1. Kopiere `custom_components/tsun_local` nach `/config/custom_components/`.
2. Starte Home Assistant neu.
3. Öffne **Einstellungen → Geräte & Dienste → Integration hinzufügen**.
4. Suche nach **TSUN Local**.

## Gerät hinzufügen

Das Gerät kann im lokalen Netzwerk gesucht oder manuell eingetragen werden. Home Assistant fragt zunächst nur nach:

- IP-Adresse des Mikrowechselrichters/Loggers;
- TCP-Port `8899` als änderbarer Standardwert;

Anschließend liest Home Assistant die numerische **Monitor SN / Logger SN** automatisch über die lokale Seite `index_cn.html` oder `status.html` des Loggers mit den werkseitigen Web-Zugangsdaten aus. Diese Daten werden nur für diese lokale Anfrage verwendet und nicht gespeichert. Der richtige Wert steht unter **Device serial number**; es handelt sich nicht um die alphanumerische **Inverter serial number**.

Ist die Seite nicht verfügbar, wurden ihre Zugangsdaten geändert oder ist der Wert nicht lesbar, zeigt dasselbe Formular ein Feld zur manuellen Eingabe der Monitor SN an. Der Wert kann von **Device serial number** auf der lokalen Statusseite oder vom Typenschild übernommen werden.

Das lokale Protokoll wird automatisch erkannt, sobald das Gerät antwortet. Die alphanumerische Seriennummer des Wechselrichters wird in der AP-Kommunikationshülle nicht verwendet.

Die Netzwerksuche prüft die für Home Assistant sichtbaren IPv4-Subnetze am gewählten TCP-Port. VLANs, geroutete Netzwerke, Container-Netzwerke oder WLAN-Client-Isolation können die automatische Suche verhindern; die manuelle Konfiguration bleibt verfügbar.

Nach dem Hinzufügen eines über die Netzwerksuche gefundenen Geräts öffnet Home Assistant automatisch eine neue Suche für den nächsten Mikrowechselrichter. Sie verwendet dieselben Netzwerke und denselben TCP-Port, blendet die gerade eingerichtete Adresse aus und endet, wenn kein weiteres Gerät übrig ist. Jeder Mikrowechselrichter erhält einen unabhängigen Eintrag mit automatisch erkannter oder manuell eingegebener Monitor SN, eigenen Entitäten und Abfrageintervallen. Vollständige Geräteabfragen verwenden eine gemeinsame Sperre und laufen nacheinander.

## Abfrageeinstellungen

Öffne unter **Einstellungen → Geräte & Dienste → TSUN Local** die Option **Konfigurieren** des betreffenden Geräts:

- normales Intervall: 10 Sekunden bis 5 Minuten, standardmäßig 20 Sekunden;
- Wiederholungsintervall nach einem Kommunikationsfehler: 10 Sekunden bis 5 Minuten, standardmäßig 20 Sekunden;
- Offline-/Nachtintervall: 1 bis 60 Minuten, standardmäßig 5 Minuten;
- aufeinanderfolgende Fehler bis offline: 1 bis 20, standardmäßig 3.

Mit **Neu konfigurieren** können IP-Adresse und TCP-Port geändert werden, ohne die vorhandenen Entitäten zu löschen.

Die Schaltfläche **Daten aktualisieren** startet sofort eine vollständige Abfrage des betreffenden Mikrowechselrichters, ohne die konfigurierten Intervalle zu ändern. Wird gerade ein anderes TSUN-Gerät gelesen, wartet die manuelle Aktualisierung bis zum Ende dieser Abfrage.

## Entitäten

Die Integration erstellt für jeden eingerichteten Mikrowechselrichter ein Home-Assistant-Gerät. Technische Entitätskennungen bleiben englisch, während die angezeigten Namen übersetzt werden.

Neue Kennungen verwenden stabile englische Schlüssel wie `ac_power`, `pv1_current` und `pv1_energy_total`. Eine bereits von einer älteren Version in Home Assistant gespeicherte Kennung wird absichtlich nicht automatisch umbenannt, da dies Dashboards und Automatisierungen beschädigen könnte; sie kann bei Bedarf in den Entitätseinstellungen manuell geändert werden.

Verfügbar sind:

- AC-Momentanwerte und Energiezähler;
- fünf Messwerte je erkanntem PV-Eingang;
- berechnete DC-Gesamtleistung;
- vier Kommunikationsdiagnosen sowie Logger-Firmwareversion und MAC-Adresse als Diagnoseentitäten;
- ein binärer Verbindungssensor **Mikrowechselrichter online**;
- ein globaler Wechselrichteralarm und protokollspezifische rohe Alarmregister;
- eine manuelle Schaltfläche **Daten aktualisieren**.

Die PV-Erkennung erfolgt schrittweise. TITAN kann mit der aktuellen 1511-Karte PV1 bis PV6 bereitstellen. GEN3/GEN3 PLUS kann mit der aktuellen 02B0-Karte PV1 bis PV4 bereitstellen. Ein einmal erkannter Eingang bleibt in Home Assistant registriert.

### Wechselrichteralarme

Interne Alarme werden getrennt von Kommunikationsfehlern behandelt:

- TITAN/1511 stellt vier globale Wörter, vier sekundäre Wörter und ein Rohwort je erkanntem PV-Eingang bereit;
- GEN3/GEN3 PLUS/02B0 stellt die vier Rohregister ERR1 bis ERR4 bereit;
- jede Rohdiagnose zeigt Dezimalwert, Hexadezimalwert und Registeradresse;
- jeder Wert ungleich null aktiviert den globalen Binärsensor **Wechselrichteralarm**;
- wenn der vollständige Alarmblock nicht gelesen werden kann, wird der globale Status nicht verfügbar, statt fälschlich Entwarnung zu melden.

Die veröffentlichten Handbücher beschreiben Fehlerkategorien, aber bisher wurde keine öffentliche und verlässliche Register-/Bit-Zuordnung für alle unterstützten Familien gefunden. Unbekannte Werte bleiben deshalb roh und erhalten keine unbestätigte Fehlerbeschreibung.

Zu den dokumentierten Kategorien gehören ungewöhnliche PV-Spannungen oder -Ströme, fehlende oder ungewöhnliche Netzspannung/-frequenz, Übertemperatur, Erdschluss- oder Isolationsfehler und interne Wechselrichterfehler. Diese Kategorien dienen nur zur Information, bis ihre Beziehung zu jedem Rohregister bestätigt ist.

## Nacht- und Offline-Betrieb

Wenn der solarbetriebene Mikrowechselrichter nachts nicht mehr antwortet:

Bis zum konfigurierbaren Fehlerschwellenwert bleiben die letzten Werte verfügbar und Wiederholungen verwenden das Fehlerintervall. Beim Erreichen des Schwellenwerts (standardmäßig 3 Fehler) geht das Gerät offline und verwendet das Offline-/Nachtintervall. Die erste erfolgreiche Antwort setzt den Zähler sofort auf null zurück und stellt das normale Intervall wieder her.

- Momentanwerte für Spannung, Strom, Leistung und Frequenz werden nicht verfügbar;
- Alarmstatus und rohe Alarmregister werden nicht verfügbar;
- Tages- und Gesamtenergiezähler behalten den letzten bekannten Wert;
- **Mikrowechselrichter online** wird ausgeschaltet und der Fehlerzähler steigt;
- das langsamere Offline-/Nachtintervall wird verwendet;
- nach der ersten erfolgreichen Antwort wird das normale Intervall wiederhergestellt.

## Lokaler Betrieb und Cloud-Zugriff

TSUN Local selbst kontaktiert keinen TSUN-Cloud-Dienst. Die Telemetrie wird direkt vom lokalen Gerät gelesen.

Die eigene Internet- oder Cloud-Kommunikation des Mikrowechselrichters wird dadurch nicht deaktiviert. Eine vollständige Internet-Isolation muss am Router oder an der Firewall eingerichtet werden, wobei der lokale Zugriff von Home Assistant auf IP-Adresse und TCP-Port erhalten bleiben muss.

## Community-Tests und Diagnosen

Mit 🧪 markierte Modelle können tatsächlich getestet werden. Erfolgreiche und fehlgeschlagene Versuche sind gleichermaßen hilfreich: Unterschiede zwischen Modellen oder Firmware-Versionen lassen sich nur durch Rückmeldungen von echter Hardware bestätigen.

Wenn die Integration bereits eingerichtet ist:

1. Öffne **Einstellungen → Geräte & Dienste → TSUN Local**.
2. Aktiviere im Integrationsmenü die Debug-Protokollierung, stelle das Problem einmal nach und deaktiviere die Protokollierung anschließend wieder.
3. Lade die Diagnose auf derselben Integrations- oder Geräteseite herunter.
4. Erstelle einen [Kompatibilitätsbericht](https://github.com/jptstar/tsun-local/issues/new/choose) mit genauem Modell, Firmware-Version, TSUN-Local-Version und der heruntergeladenen Datei.

Wenn die Einrichtung nicht abgeschlossen werden kann, starte die eigenständige Aufzeichnung aus einer Kopie dieses Repositorys:

```bash
python3 tools/diagnose_device.py --host GERAETE_IP
```

Die Monitor SN wird interaktiv abgefragt und nicht im Befehlsverlauf gespeichert. Die erzeugte Datei `tsun_local_diagnostic.json` enthält dekodierte Messwerte und eine kurze Ringspur der internen Protokollanfragen und -antworten. Sie enthält **weder Geräte-IP noch Monitor SN noch Logger-MAC-Adresse noch AP-Hülle**. Prüfe die Datei vor dem Teilen, da Produktions- und Energiewerte sichtbar bleiben.

Die aufgezeichneten Antworten können ohne das physische Gerät lokal erneut ausgewertet werden:

```bash
python3 tools/replay_diagnostic.py tsun_local_diagnostic.json
```

Die verfügbaren Registerkarten sind eine solide Ausgangsbasis, garantieren aber kein identisches Verhalten jedes ungeprüften Modells oder jeder Firmware-Version. Durch Aufzeichnung und Wiedergabe werden gezielte Kompatibilitätskorrekturen möglich, ohne Fernzugriff auf das Netzwerk anderer Nutzer.

## Mögliche nächste Erweiterungen

Die folgenden Ideen sind bewusst noch nicht aktiviert und benötigen vor einer Umsetzung eine Validierung:

- Netzschutzschwellen als schreibgeschützte Diagnoseentitäten;
- der 02B0-Ausgangskoeffizient als schreibgeschützter Prozentwert;
- Home-Assistant-Benachrichtigungen oder Reparaturhinweise für dauerhafte Alarme;
- übersetzte Fehlerbeschreibungen nach Bestätigung der Register-/Bit-Zuordnung;
- weitere lokale Adapter für künftige TSUN-Mikrowechselrichterfamilien.

Schreib- oder Steuerbefehle werden nicht ohne ausdrückliche Schutzmaßnahmen und Validierung auf echter Hardware hinzugefügt.

## Autor

Jean-Philippe TESTART (`jptstar`)

## Lizenz

Copyright © 2026 Jean-Philippe TESTART (jptstar).

Dieses Projekt wird unter der **GNU General Public License v3.0 oder höher** (`GPL-3.0-or-later`) veröffentlicht. Geänderte oder weiterverteilte Versionen müssen die Lizenzbedingungen einhalten und die Copyright- und Lizenzhinweise beibehalten. Siehe [LICENSE](LICENSE).

Die Lizenz gilt ausschließlich für diese unabhängige Implementierung. Sie gewährt keine Rechte an Marken, Logos, Software oder Produkten von TSUN. Dieses Projekt bleibt inoffiziell und unabhängig von TSUN.
