<p align="center"><a href="../README.md">English</a> · <a href="README_FR.md">Français</a> · <a href="README_DE.md">Deutsch</a> · <a href="README_NL.md">Nederlands</a> · <a href="README_IT.md">Italiano</a> · <a href="README_ES.md">Español</a> · <strong>Polski</strong> · <a href="README_ZH.md">简体中文</a></p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Twój falownik. Twoja sieć. Twoje dane.</h3>
<p align="center"><strong>Automatyczne wykrywanie · Lokalnie · Tylko odczyt · Bez chmury · Bez proxy</strong><br><strong>1.6.2</strong></p>

## Zgodność

| Protocol | Family | Validated hardware | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validated** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MS300** · **TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2** | ✅ **Validated** |
| **1097** | GEN4 | **Sunology PLAY2 (GEN4)** | ✅ **Validated** |

- **1511 — Likely compatible:** `TSOL-MP2250` · `TSOL-MS3000`
- **02B0 — Likely compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800`
- **1097 — Likely compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

Zweryfikowane strony: [TSOL-MS300](https://jptstar.github.io/tsun-local/tsol-ms300-home-assistant.html) · [TSOL-MX500](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html) · [TSOL-MS800](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html) · [TSOL-MS2000](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html) · [Sunology PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)

## Instalacja

Zainstaluj TSUN Local przez HACS, uruchom ponownie Home Assistant i dodaj integrację w **Ustawienia → Urządzenia i usługi**.

## Diagnostyka

Utrzymywane są dwa publiczne pakiety:

- **Windows**: [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)
- **Python 3.10+**: [TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip)

Diagnostyka działa wyłącznie w trybie odczytu. Przed przechwytywaniem wyłącz odpowiedni wpis TSUN Local, a po zakończeniu włącz go ponownie. Wysłanie anonimowego raportu zawsze wymaga wyraźnej zgody.

📚 [Przewodnik diagnostyczny](HARDWARE_DUMP.md) · [Badania PLAY2](PLAY2_LOCAL_RESEARCH.md) · [Encje](ENTITIES.md) · [Walidacja MP3000](MP3000_FIELD_VALIDATION.md)

## Credits

Publiczne odniesienie krzyżowe z [`ha-solarman`](https://github.com/davidrapan/ha-solarman). Niezależna walidacja sprzętu m.in. przez **dca31** i **paloindici**. Pełne podziękowania: [contributors](contributors.html).

Niezależny projekt utrzymywany przez **Jean-Philippe TESTART (`jptstar`)**. GPL-3.0-or-later.
