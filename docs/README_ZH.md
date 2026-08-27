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
<p align="center">在 Home Assistant 中直接本地访问兼容的 TSUN 微型逆变器。<br><strong>1.5.3</strong></p>

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
| **1097** | GEN3 / GEN3 PLUS | 🧪 **实验性** |

> [!TIP]
> **未列出并不代表不支持。** 如果你的逆变器使用 **1511、02B0 或 1097**，它可能已经能够工作。

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration">
    <img alt="将 TSUN Local 添加到 HACS" src="https://my.home-assistant.io/badges/hacs_repository.svg">
  </a>
</p>

---

## 一览

| | TSUN Local 可提供的数据 |
|---|---|
| ☀️ **PV** | 电压 · 电流 · 功率 · 当日发电量 · 总发电量 |
| ⚡ **AC** | 电压 · 电流 · 频率 · 功率 · 当日发电量 · 总发电量 |
| 🚨 **诊断** | 活动告警 · 通信 · Logger 信息 |
| 🛡️ **高级** | 电网保护 · 固件 · 逆变器诊断 · 实验性现场验证数据 |
| 🔒 **安全** | 只读 · 不向逆变器写入配置 |

📚 **[按协议查看完整实体列表](ENTITIES.md)**

---

## 兼容性

**需要 Home Assistant 2026.3.0 或更高版本。**

> [!NOTE]
> **✅ 已验证** = 已在真实硬件上使用 TSUN Local 确认。  
> **🔎 很可能兼容** = 协议系列已支持，但该具体型号尚未验证。  
> **🧪 实验性** = 已有协议支持，但仍需要更多真实设备验证。

### 1511 · TITAN — ✅ 已验证

**✅ 已验证**  
`TSOL-MP3000`

**🔎 很可能兼容**  
`TSOL-MP2250` · `TSOL-MS3000` *(TITAN 代际)*

最多 6 路 PV 输入，支持 AC/PV 遥测、能量、逆变器诊断、固件版本、告警以及高级只读电网诊断。

📚 **[MP3000 / TITAN 现场验证详情](MP3000_FIELD_VALIDATION.md)**

### 02B0 · GEN3 / GEN3 PLUS — ✅ 已验证

**✅ 已验证**  
`TSOL-MX500` · `Sunology PLAY2`

**🔎 很可能兼容**  
`TSOL-MX450` · `TSOL-MX800` · `TSOL-MX1000` · `TSOL-MX3000`  
`TSOL-MS800` · `TSOL-MS1600` · `TSOL-MS1800` · `TSOL-MS2000`

相应的 `-D` 变体在适用时也可能兼容。

支持动态 PV 输入检测、AC/PV 遥测、逆变器告警以及高级只读诊断。


已在真实设备上独立验证 **Sunology PLAY2**：Home Assistant 自动发现设备并成功完成 TSUN Local 配置。

### 1097 · GEN3 / GEN3 PLUS — 🧪 实验性

**🔎 很可能兼容**  
`TSOL-MS300` · `TSOL-MS350` · `TSOL-MS400`  
`TSOL-MS600` · `TSOL-MS700` · `TSOL-MS800`  
`TSOL-MS3000` · `TSOL-MX3000D`

协议支持已经实现，但仍需要更多真实设备验证。

> [!NOTE]
> 同一商品型号名称可能覆盖不同硬件或 Logger 代际。**对于 TSUN Local，以本地检测到的协议作为兼容性判断依据。**

---

## 🚨 MP3000 告警

TSUN Local 支持完整的 MP3000 告警位字段，同时保持 Home Assistant 界面简洁。**全部 224 个告警位置都会被保留，并在激活时进行评估。**

其中 **12 个在真实硬件上观察到的功能映射**覆盖 PV1 到 PV6 的低 PV 输入电压和 PV DSP 故障。其余 **212 个位置**保留稳定、中性的 TSUN Local 标识，直到其功能含义完成物理验证。

Home Assistant 提供一个 **逆变器告警** 状态、**活动告警** 计数，以及 **活动告警名称** 传感器。14 个完整原始告警字仍作为默认禁用的诊断实体提供，而不会创建 224 个永久实体。

---


> [!TIP]
> 活动告警也会以**本地化易读文本**显示，并带有稳定的位置代码，例如 `电网欠压 (02B0-A014)`。**Sunology PLAY2** 使用同一套精简的 02B0 告警界面；四个原始 ERR 字仍作为高级诊断保留。

## 🛡️ 高级诊断

高级实体被有意设置为 **默认禁用**。根据协议不同，其中包括电网保护值、固件、逆变器诊断以及部分实验性现场验证值。

启用方式：

**设置 → 设备与服务 → TSUN Local → 设备 → 实体 → 已禁用实体**

实验性语义映射在独立验证前会继续明确标注。未实现任何向逆变器写入配置的功能。

📚 **[MP3000 现场验证证据](MP3000_FIELD_VALIDATION.md)**  
📚 **[完整实体列表](ENTITIES.md)**

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

## 🔬 验证其他 TSUN 型号

TSUN Local 提供一个独立、注重隐私且 **严格只读** 的硬件采集工具。

**⬇️ [下载 `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

只需要 Python 3.10+。

macOS / Linux：

```bash
cd ~/Downloads
python3 tsun_dump.py --full
```

Windows：

```powershell
py tsun_dump.py --full
```

该工具可以发现兼容的 TSUN Logger、识别支持的协议系列，并为每台设备生成注重隐私的 JSON dump。它不实现任何逆变器写入操作。

对于 VLAN、定向发现、前后对比以及高级验证：

📚 **[Hardware Validation Dump Tool 指南](HARDWARE_DUMP.md)**

---

## 测试未列出的逆变器

如果 TSUN Local 检测到 `1511`、`02B0` 或 `1097`，让集成继续运行并检查发现的实体。

最有用的反馈包括准确型号、检测到的协议、固件版本、PV 输入数量，以及哪些实体返回合理数值。

> [!TIP]
> **你的逆变器可能成为下一个已验证型号。**

---

## 验证策略

TSUN Local 将已确认的硬件支持与实验性的协议研究明确区分。

只有在真实硬件上完成可重复验证后，功能名称和型号支持才会标记为已验证。仅仅与预期配置数值一致只能作为证据，而不能视为最终证明；实验性映射会一直保留标记，直到独立观察能够明确区分对应字段。

---

## 社区贡献

TSUN Local 受益于公开协议研究以及社区在真实硬件上的测试。

- **Stefan Allius / `s-allius/tsun-gen3-proxy`** — 公开的 GEN3 / 1097 协议研究，用作部分实验性映射的参考。
- **TheSmartGerman** — 真实硬件兼容性反馈。

详细来源和验证证据会与相应的协议研究一起记录。

---

## 项目

> [!IMPORTANT]
> **非官方社区项目。** TSUN Local 是独立项目，并非由 TSUN 开发、批准、认可或维护。

由 **Jean-Philippe TESTART · `jptstar`** 创建并维护  
*出于兴趣、技术好奇心以及对 Home Assistant 社区的分享而开发。*

---

## 许可证

Copyright © 2026 Jean-Philippe TESTART (`jptstar`).

依据 **GNU General Public License v3.0 或更高版本**发布。参见 [LICENSE](../LICENSE)。
