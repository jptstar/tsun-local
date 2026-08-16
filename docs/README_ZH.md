# TSUN Local 1.4.0

<p align="center">[English](../README.md) · [Français](README_FR.md) · [Deutsch](README_DE.md) · [Nederlands](README_NL.md) · [Italiano](README_IT.md) · [Español](README_ES.md) · [Polski](README_PL.md) · [简体中文](README_ZH.md)</p>

### 你的逆变器。你的网络。你的数据。
## 本地。只读。无需云端。无需代理。

> **你的 TSUN 逆变器可能已经可以使用**  
> 未列出的型号并不代表不受支持。

| Protocol | Hardware / family | Status |
|---|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ 已在真实硬件上验证 |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ 已在真实硬件上验证 |
| **1097** | GEN3 family | 🧪 实验性 |

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

**安装 TSUN Local，让它识别协议，然后查看逆变器可提供的数据。**

## 高级诊断

只读的电网和逆变器参数默认关闭，可在 Home Assistant 中逐项启用。

- **1511:** grid protection diagnostics
- **02B0:** grid protection diagnostics + output coefficient
- **1097:** protocol/inverter versions, temperature, insulation impedance RX/RY, country/profile code and designed power

## 兼容性

### ✅ 已在真实硬件上验证
- **TSOL-MP3000** — 1511 — 6 PV inputs
- **TSOL-MX500** — 02B0 — 1 PV input

### 🔎 值得尝试
MP2250 · MS3000 · MX400 · MX450 · MX800 · MX900 · MX1000 · MX2250 · MS300 · MS350 · MS400 · MS600 · MS700 · MS800 · MS1600 · MS1800 · MS2000 and corresponding `-D` variants where applicable.

### 🧪 1097 — 实验性

有其他 TSUN 型号？试试看——它可能成为下一个已验证设备。

---

**Jean-Philippe TESTART (`jptstar`)** · Unofficial independent community project · GPL-3.0-or-later

实验性 1097 映射参考了 Stefan Allius / s-allius/tsun-gen3-proxy 的公开协议研究，并针对 TSUN Local 进行了适配。
