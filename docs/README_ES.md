<p align="center"><a href="../README.md">English</a> · <a href="README_FR.md">Français</a> · <a href="README_DE.md">Deutsch</a> · <a href="README_NL.md">Nederlands</a> · <a href="README_IT.md">Italiano</a> · <strong>Español</strong> · <a href="README_PL.md">Polski</a> · <a href="README_ZH.md">简体中文</a></p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">Tu inversor. Tu red. Tus datos.</h3>
<p align="center"><strong>Detección automática · Local · Solo lectura · Sin nube · Sin proxy</strong><br><strong>1.6.2</strong></p>

## Compatibilidad

| Protocol | Family | Validated hardware | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validated** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MS300** · **TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2** | ✅ **Validated** |
| **1097** | GEN4 | **Sunology PLAY2 (GEN4)** | ✅ **Validated** |

- **1511 — Likely compatible:** `TSOL-MP2250` · `TSOL-MS3000`
- **02B0 — Likely compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800`
- **1097 — Likely compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

Páginas validadas: [TSOL-MS300](https://jptstar.github.io/tsun-local/tsol-ms300-home-assistant.html) · [TSOL-MX500](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html) · [TSOL-MS800](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html) · [TSOL-MS2000](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html) · [Sunology PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)

## Instalación

Instala TSUN Local desde HACS, reinicia Home Assistant y añade la integración desde **Ajustes → Dispositivos y servicios**.

## Diagnóstico

Se mantienen dos paquetes públicos:

- **Windows**: [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)
- **Python 3.10+**: [TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip)

El diagnóstico es estrictamente de solo lectura. Desactiva la entrada TSUN Local afectada antes de la captura y vuelve a activarla después. El envío del informe anonimizado requiere consentimiento explícito.

📚 [Guía de diagnóstico](HARDWARE_DUMP.md) · [Investigación PLAY2](PLAY2_LOCAL_RESEARCH.md) · [Entidades](ENTITIES.md) · [Validación MP3000](MP3000_FIELD_VALIDATION.md)

## Créditos

Referencia pública cruzada con [`ha-solarman`](https://github.com/davidrapan/ha-solarman). Validación independiente de hardware, entre otros, por **dca31** y **paloindici**. Créditos completos: [contributors](contributors.html).

Proyecto independiente mantenido por **Jean-Philippe TESTART (`jptstar`)**. GPL-3.0-or-later.
