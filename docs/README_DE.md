<p align="center"><a href="../README.md">English</a> · <a href="README_FR.md">Français</a> · <strong>Deutsch</strong> · <a href="README_NL.md">Nederlands</a> · <a href="README_IT.md">Italiano</a> · <a href="README_ES.md">Español</a> · <a href="README_PL.md">Polski</a> · <a href="README_ZH.md">简体中文</a></p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Dein Wechselrichter. Dein Netzwerk. Deine Daten.</h3>
<p align="center"><strong>Automatische Erkennung · Lokal · Nur Lesen · Keine Cloud · Kein Proxy</strong><br><strong>1.6.2</strong></p>

## Kompatibilität

| Protocol | Family | Validated hardware | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validated** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MS300** · **TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2** | ✅ **Validated** |
| **1097** | GEN4 | **Sunology PLAY2 (GEN4)** | ✅ **Validated** |

- **1511 — Likely compatible:** `TSOL-MP2250` · `TSOL-MS3000`
- **02B0 — Likely compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800`
- **1097 — Likely compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

Validierte Seiten: [TSOL-MS300](https://jptstar.github.io/tsun-local/tsol-ms300-home-assistant.html) · [TSOL-MX500](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html) · [TSOL-MS800](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html) · [TSOL-MS2000](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html) · [Sunology PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)

## Installation

TSUN Local über HACS installieren, Home Assistant neu starten und die Integration unter **Einstellungen → Geräte & Dienste** hinzufügen.

## Diagnose

Zwei öffentliche Pakete werden gepflegt:

- **Windows**: [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)
- **Python 3.10+**: [TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip)

Die Diagnose ist streng schreibgeschützt. Den betroffenen TSUN-Local-Eintrag vor der Aufnahme deaktivieren und danach wieder aktivieren. Ein anonymisierter Upload erfolgt nur nach ausdrücklicher Zustimmung.

📚 [Diagnosehandbuch](HARDWARE_DUMP.md) · [PLAY2-Forschung](PLAY2_LOCAL_RESEARCH.md) · [Entitäten](ENTITIES.md) · [MP3000-Validierung](MP3000_FIELD_VALIDATION.md)

## Credits

Öffentliche Gegenprüfung mit [`ha-solarman`](https://github.com/davidrapan/ha-solarman). Unabhängige Hardwarevalidierung unter anderem durch **dca31** und **paloindici**. Vollständige Credits: [contributors](contributors.html).

Unabhängiges Projekt von **Jean-Philippe TESTART (`jptstar`)**. GPL-3.0-or-later.
