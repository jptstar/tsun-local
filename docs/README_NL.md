<p align="center"><a href="../README.md">English</a> · <a href="README_FR.md">Français</a> · <a href="README_DE.md">Deutsch</a> · <strong>Nederlands</strong> · <a href="README_IT.md">Italiano</a> · <a href="README_ES.md">Español</a> · <a href="README_PL.md">Polski</a> · <a href="README_ZH.md">简体中文</a></p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Jouw omvormer. Jouw netwerk. Jouw data.</h3>
<p align="center"><strong>Automatische detectie · Lokaal · Alleen-lezen · Geen cloud · Geen proxy</strong><br><strong>1.6.2</strong></p>

## Compatibiliteit

| Protocol | Family | Validated hardware | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validated** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MS300** · **TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2** | ✅ **Validated** |
| **1097** | GEN4 | **Sunology PLAY2 (GEN4)** | ✅ **Validated** |

- **1511 — Likely compatible:** `TSOL-MP2250` · `TSOL-MS3000`
- **02B0 — Likely compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800`
- **1097 — Likely compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

Gevalideerde pagina's: [TSOL-MS300](https://jptstar.github.io/tsun-local/tsol-ms300-home-assistant.html) · [TSOL-MX500](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html) · [TSOL-MS800](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html) · [TSOL-MS2000](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html) · [Sunology PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)

## Installatie

Installeer TSUN Local via HACS, herstart Home Assistant en voeg de integratie toe via **Instellingen → Apparaten & diensten**.

## Diagnostiek

Er worden twee openbare pakketten onderhouden:

- **Windows**: [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)
- **Python 3.10+**: [TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip)

De diagnose is strikt alleen-lezen. Schakel de betrokken TSUN Local-configuratie uit vóór de capture en daarna weer in. Upload van het geanonimiseerde rapport vereist altijd expliciete toestemming.

📚 [Diagnosehandleiding](HARDWARE_DUMP.md) · [PLAY2-onderzoek](PLAY2_LOCAL_RESEARCH.md) · [Entiteiten](ENTITIES.md) · [MP3000-validatie](MP3000_FIELD_VALIDATION.md)

## Credits

Openbare kruisreferentie met [`ha-solarman`](https://github.com/davidrapan/ha-solarman). Onafhankelijke hardwarevalidatie onder andere door **dca31** en **paloindici**. Volledige credits: [contributors](contributors.html).

Onafhankelijk project onderhouden door **Jean-Philippe TESTART (`jptstar`)**. GPL-3.0-or-later.
