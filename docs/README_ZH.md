<p align="center"><a href="../README.md">English</a> · <a href="README_FR.md">Français</a> · <a href="README_DE.md">Deutsch</a> · <a href="README_NL.md">Nederlands</a> · <a href="README_IT.md">Italiano</a> · <a href="README_ES.md">Español</a> · <a href="README_PL.md">Polski</a> · <strong>简体中文</strong></p>

<h1 align="center">TSUN Local</h1>
<h3 align="center">你的逆变器。你的网络。你的数据。</h3>
<p align="center"><strong>自动发现 · 本地 · 只读 · 无云端 · 无代理</strong><br><strong>1.6.2</strong></p>

## 兼容性

| Protocol | Family | Validated hardware | Status |
|:---:|---|---|:---:|
| **1511** | TITAN | **TSOL-MP3000** | ✅ **Validated** |
| **02B0** | GEN3 / GEN3 PLUS | **TSOL-MS300** · **TSOL-MX500** · **TSOL-MS800** · **TSOL-MS2000** · **Sunology PLAY2** | ✅ **Validated** |
| **1097** | GEN4 | **Sunology PLAY2 (GEN4)** | ✅ **Validated** |

- **1511 — Likely compatible:** `TSOL-MP2250` · `TSOL-MS3000`
- **02B0 — Likely compatible:** `TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000` · `TSOL-MS1600` · `TSOL-MS1800`
- **1097 — Likely compatible:** `TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400` · `TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800` · `TSOL-MS3000` · `TSOL-MX3000D`

已验证页面：[TSOL-MS300](https://jptstar.github.io/tsun-local/tsol-ms300-home-assistant.html) · [TSOL-MX500](https://jptstar.github.io/tsun-local/tsol-mx500-home-assistant.html) · [TSOL-MS800](https://jptstar.github.io/tsun-local/tsol-ms800-home-assistant.html) · [TSOL-MS2000](https://jptstar.github.io/tsun-local/tsol-ms2000-home-assistant.html) · [Sunology PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)

## 安装

通过 HACS 安装 TSUN Local，重启 Home Assistant，然后在 **设置 → 设备与服务** 中添加集成。

## 诊断

维护两个公开软件包：

- **Windows**：[TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)
- **Python 3.10+**：[TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip)

诊断严格只读。捕获前请禁用相关 TSUN Local 配置项，完成后重新启用。匿名报告上传始终需要明确同意。

📚 [诊断指南](HARDWARE_DUMP.md) · [PLAY2 研究](PLAY2_LOCAL_RESEARCH.md) · [实体](ENTITIES.md) · [MP3000 验证](MP3000_FIELD_VALIDATION.md)

## 致谢

公开交叉参考 [`ha-solarman`](https://github.com/davidrapan/ha-solarman)。独立硬件验证者包括 **dca31** 和 **paloindici**。完整致谢见 [contributors](contributors.html)。

独立项目，由 **Jean-Philippe TESTART (`jptstar`)** 维护。GPL-3.0-or-later。
