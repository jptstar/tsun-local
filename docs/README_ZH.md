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
<p align="center">在 Home Assistant 中直接本地访问兼容的 TSUN 微型逆变器。<br><strong>1.5.1</strong></p>

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
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500** | ✅ **已验证** |
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
| 🚨 **诊断** | 逆变器告警 · 活动告警数量和名称 · DSP/QCPU 固件版本 |
| 🛡️ **高级** | 电网保护阈值与延时 · 10 项额外 A1/21 现场验证诊断 · 国家/配置原始候选值 · 温度 |

### 02B0 · GEN3 / GEN3 PLUS — ✅ 已验证

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
| 🚨 **诊断** | 逆变器告警 · 活动告警数量和名称 · DSP/QCPU 固件版本 |
| 🛡️ **高级** | 电网保护诊断 · 功率水平 (%) |

### 1097 · GEN3 / GEN3 PLUS — 🧪 实验性

**🔎 很可能兼容**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

> [!NOTE]
> 公开的 GEN3 研究通常将这些设备与 **R17 / R47** 序列号系列关联。在更多真实硬件上确认之前，TSUN Local 的 **1097** 协议兼容性仍属于实验性支持。

| | 可用数据 |
|---|---|
| ☀️ **PV** | 标准 PV 遥测 |
| ⚡ **AC** | 标准逆变器 / AC 遥测 |
| 🚨 **诊断** | 可用的逆变器诊断数据 |
| 🛡️ **高级** | 协议版本 · 逆变器版本 · 温度 · 绝缘 RX/RY · 功率水平（实验） · 国家/配置原始值 · 设计功率 |

> **🔎 很可能兼容并不等于已验证。** 这表示 TSUN Local 已实现相应协议系列，因此该设备是很有希望的兼容候选型号。

---

## 1.4.1 中基于实机验证的修正

在 MP3000 / 1511 与 MX500 / 02B0 实机上验证后，1.4.1 重新发布前进一步修正了以下诊断项：

- 电网保护时间原生继续使用**秒**；早期 beta 版本自动保存的 `ms` 显示单位会迁移回 `s`；
- 在已验证的 MP3000 上，日出、日落以及光照极低时观察到的原始位 `0x2000`（`8192`）仍会显示、计数，并使用中性的本地代码报告；在通过控制硬件确认其确切含义之前，运行状态仍显示为**待机 — 光照输入不足**；
- TITAN 寄存器 **3017** 和 **3028** 现在分别按 **逆变器温度** 和 **逆变器环境温度** 解码，公式为 `raw - 40 °C`；原始值仍保留用于验证；
- 02B0 寄存器 `0x202C` 现在显示为 **功率水平**，采用已确认的 `raw × 100 / 1024` 比例（`1024 = 100 %`）；

---

## 🆕 TSUN Local 1.5.1

**1.5.1** 将 1.5.0 的完整 MP3000 告警界面与 beta1 至 beta4 的修正合并为一个稳定版本：

- 保留全部 **224 个 MP3000 告警位置**；其中 12 个功能对应关系来自直接硬件观察；
- 新增独立的**活动告警名称**传感器，并随 Home Assistant 语言本地化；
- 修正 logger Wi-Fi RSSI 回退读取，可继续读取到 `/status.html`；
- 新增 10 项只读 A1/21 现场验证诊断以及国家/配置原始候选值；
- `0x07EF`：`4000 → 40.00 %/Hz`，候选比例为 `×0.01`；
- 本地固件版本 **DSP V1.1.72**、**QCPU1 V1.1.54**、**QCPU2 V1.1.54**；在未找到本地 1511 寄存器前不发布 FCPU；
- 之前未确认的 MP3000 功率水平候选实体保持删除；
- 技术 entity ID 保持英文，显示名称覆盖全部八种语言。

尚未独立确认的 A1/21 语义映射继续使用状态：**LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING**。
---

## 🚨 MP3000 报警目录

14 个报警字中的全部 **224 个位置**都会被纳入、计数，并在激活时显示。已有 **12 个功能对应关系**来自真实硬件上的直接观察；其余 **212 个位置**使用唯一且中性的 TSUN Local 代码，并需要在合适的控制硬件上进行物理验证。任何激活位置都不会被忽略。八种语言的文本均为 TSUN Local 的独立表述，不会被宣称为官方服务器译文。

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

## 验证原则

只有在真实硬件上完成可重复验证后，功能名称和型号支持才会被标记为已验证。

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
