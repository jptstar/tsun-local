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
<h3 align="center">你的逆变器。你的网络。你的数据。</h3>
<p align="center"><strong>本地。只读。无需云端。无需代理。</strong></p>
<p align="center">在 Home Assistant 中直接本地访问兼容的 TSUN 微型逆变器。<br><strong>1.4.0</strong></p>

<p align="center">
  <a href="https://github.com/jptstar/tsun-local/releases"><img alt="GitHub Release" src="https://img.shields.io/github/v/release/jptstar/tsun-local"></a>
  <a href="https://github.com/hacs/integration"><img alt="HACS" src="https://img.shields.io/badge/HACS-Custom-41BDF5"></a>
  <a href="../LICENSE"><img alt="GPL-3.0-or-later" src="https://img.shields.io/badge/License-GPL--3.0--or--later-blue"></a>
</p>

---

## 你的 TSUN 逆变器可能已经可以使用

TSUN Local 支持 **三种 TSUN 本地协议系列**。

| 协议 | 系列 / 已验证参考型号 | 状态 |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ **已验证** |
| **02B0** | GEN3 PLUS · **TSOL-MX500** | ✅ **已验证** |
| **1097** | GEN3 | 🧪 **实验性** |

> [!TIP]
> **未列出并不代表不支持。** 如果你的逆变器使用 **1511、02B0 或 1097**，它可能已经能够工作。

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="将 TSUN Local 添加到 HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

<p align="center"><strong>安装它。让 TSUN Local 识别协议。查看你的逆变器可以提供哪些数据。</strong></p>

---

## 一览

| | TSUN Local 可提供的数据 |
|---|---|
| ☀️ **PV** | 电压 · 电流 · 功率 · 当日发电量 · 总发电量 |
| ⚡ **AC** | 电压 · 电流 · 频率 · 功率 · 当日发电量 · 总发电量 |
| 🚨 **诊断** | 告警 · 通信 · Logger 信息 |
| 🛡️ **高级** | 电网保护 · 逆变器诊断 · 默认禁用 |
| 🔒 **安全** | 只读 · 不向逆变器写入配置 |

📚 **[按协议查看完整实体列表](ENTITIES.md)** — **1511、02B0 和 1097** 的传感器、二进制传感器和按钮。

---

## 兼容性

**需要 Home Assistant 2026.3.0 或更高版本。**

> [!NOTE]
> **✅ 已验证** = 已在真实硬件上使用 TSUN Local 确认。  
> **🔎 很可能兼容** = 协议系列已支持，但该具体型号尚未使用 TSUN Local 验证。  
> **🧪 实验性** = 已有协议支持，但仍需要更多真实设备验证。

### 1511 · TITAN — ✅ 已验证

**✅ 已验证**  
`TSOL-MP3000`

**🔎 很可能兼容**  
`TSOL-MP2250` · `TSOL-MS3000` *(TITAN 代际)*

| | 可用数据 |
|---|---|
| ☀️ **PV** | 最多 6 路输入 · 电压 · 电流 · 功率 · 当日及总发电量 |
| ⚡ **AC** | 电压 · 电流 · 频率 · 功率 · 当日及总发电量 |
| 🚨 **诊断** | 逆变器告警 |
| 🛡️ **高级** | 电网保护阈值及时间参数诊断 |

### 02B0 · GEN3 PLUS — ✅ 已验证

**✅ 已验证**  
`TSOL-MX500`

**🔎 很可能兼容**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`  
相应的 `-D` 变体在适用时也可能兼容。

> [!NOTE]
> 公开的 GEN3 PLUS 研究通常将这些设备与 **Y17 / Y47** 序列号系列关联。这有助于区分名称相同、但属于较早 GEN3 代际的型号。

| | 可用数据 |
|---|---|
| ☀️ **PV** | 动态 PV 输入检测 · 电压 · 电流 · 功率 · 能量 |
| ⚡ **AC** | 电压 · 电流 · 频率 · 功率 · 能量 |
| 🚨 **诊断** | 逆变器告警 |
| 🛡️ **高级** | 电网保护诊断 · 输出系数 |

### 1097 · GEN3 — 🧪 实验性

**🔎 很可能兼容**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000`

> [!NOTE]
> 公开的 GEN3 研究通常将这些设备与 **R17 / R47** 序列号系列关联。在更多真实硬件上确认之前，TSUN Local 的 **1097** 协议兼容性仍属于实验性支持。

| | 可用数据 |
|---|---|
| ☀️ **PV** | 标准 PV 遥测 |
| ⚡ **AC** | 标准逆变器 / AC 遥测 |
| 🚨 **诊断** | 可用的逆变器诊断数据 |
| 🛡️ **高级** | 协议版本 · 逆变器版本 · 温度 · 绝缘 RX/RY · 国家/配置原始值 · 设计功率 |

> **🔎 很可能兼容并不等于已验证。** 这表示 TSUN Local 已实现相应协议系列，因此该设备是很有希望的兼容候选型号。

---

## 🛡️ 高级诊断

高级实体被有意设置为 **默认禁用**。这样可以保持普通设备页面简洁，同时在需要时仍可启用更深入的技术信息。

启用方式：

**设置 → 设备与服务 → TSUN Local → 设备 → 实体 → 已禁用实体**

未实现任何向逆变器写入配置的功能。

---

## 安装

### HACS

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="将 TSUN Local 添加到 HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

或者在 **HACS → 自定义仓库 → Integration** 中添加 `https://github.com/jptstar/tsun-local`，安装 **TSUN Local**，然后重启 Home Assistant。

### 手动安装

将 `custom_components/tsun_local` 复制到 `/config/custom_components/`，重启 Home Assistant，然后在 **设置 → 设备与服务** 中添加 **TSUN Local**。

---

## 工作方式

```text
TSUN 逆变器
     │
     │ 本地网络
     ▼
 TSUN Local
     │
     ▼
Home Assistant
```

**数据路径中无需云端。无需代理。无需远程运行服务。不向逆变器写入配置。**

仅进行直接本地轮询。

---

## 测试其他 TSUN 型号

你的逆变器不一定需要出现在上面的列表中。

如果 TSUN Local 识别出以下任一协议：

```text
1511
02B0
1097
```

让集成运行并检查发现的实体。

> [!TIP]
> **你的逆变器可能成为下一个已验证型号。** 有用的反馈包括准确型号、检测到的协议、PV 输入数量、固件版本，以及哪些实体返回合理数值。

---

## TSUN Local 1.4

### 覆盖范围更广的 TSUN Local

1.4 版本让 TSUN Local 从单个已知型号的支持，扩展到 **协议系列级兼容性**。

| | |
|---|---|
| 🔌 | **1511 · 02B0 · 1097** |
| 🔍 | 自动协议识别 |
| ☀️ | 渐进式 / 动态 PV 输入检测 |
| 📊 | 更丰富的本地遥测 |
| 🛡️ | 高级只读诊断 |
| 🌍 | 8 种语言 |
| 🧪 | 更容易测试新的 TSUN 型号 |

---

## 逆向分析与验证

1511 和 02B0 的实现来自 **独立的本地协议分析、真实设备观察和硬件验证**。

兼容候选型号与真正完成验证的硬件会被明确区分。

---

## 贡献

TSUN Local 也受益于社区贡献：

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — 公开的 1097 协议研究，为 TSUN Local 使用的实验性映射提供了参考。
- **TheSmartGerman** — 对 **TSOL-MP3000 / 1511** 的真实硬件测试和兼容性反馈，在此过程中意外检测到了 **1097** 协议。

---

## 项目

> [!IMPORTANT]
> **非官方社区项目。** TSUN Local 是独立项目，并非由 TSUN 开发、批准、背书或维护。

创建和维护者：**Jean-Philippe TESTART · `jptstar`**  
*出于兴趣、技术好奇心以及对 Home Assistant 社区的分享而开发。*

---

## 许可证

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

根据 **GNU General Public License v3.0 或更高版本** 发布。参见 [LICENSE](../LICENSE)。
