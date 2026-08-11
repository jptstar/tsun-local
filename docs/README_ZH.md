# TSUN Local — Home Assistant 本地集成

[English](../README.md) | [Français](README_FR.md) | [Deutsch](README_DE.md) | [Nederlands](README_NL.md) | [Italiano](README_IT.md) | [Español](README_ES.md) | [Polski](README_PL.md) | [简体中文](README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="独立的 TSUN Local 图标">
</p>

> **非官方项目** — 此独立社区集成并非由 TSUN 开发、认可或维护，也与 TSUN 没有任何关联。TSUN 及其产品名称归各自权利人所有。有关此集成的支持请求应提交给作者，而不是 TSUN。

**TSUN Local** 可通过本地网络将兼容的 TSUN 微型逆变器直接接入 Home Assistant，无需代理服务器或云服务。版本 1.1.5 支持已在真实设备上验证的 **TSOL-MP3000** 和 **MX500**，并为其他等待验证的 **TITAN**、**GEN3** 和 **GEN3 PLUS** 型号提供支持。

**作者：Jean-Philippe TESTART（jptstar）**

## 项目性质与支持

TSUN Local 是一个 Home Assistant 集成，最初是我出于兴趣并为个人使用而开发的。由于许多用户难以与 TITAN 微型逆变器建立本地连接，我将此集成公开提供，希望尽可能多的人能够从中受益。

如果我收到有关特定型号的反馈和诊断信息，我愿意投入一些时间来改进兼容性并修复错误。不过，TSUN Local 仍然是我的个人爱好和业余项目，并非我的主要工作。因此，我有时可能需要较长时间才能回复或发布修复。

## 许可证

Copyright © 2026 Jean-Philippe TESTART (jptstar).

本项目依据 **GNU General Public License v3.0 或更高版本**（`GPL-3.0-or-later`）发布。修改或再分发的版本必须遵守此许可证，并保留版权和许可证声明。请参阅 [LICENSE](../LICENSE)。

该许可证仅涵盖此独立实现，不授予任何 TSUN 商标、徽标、软件或产品的权利。本项目始终为非官方项目，与 TSUN 无任何关联。

## 版本

发布版本遵循 `MAJOR.MINOR.PATCH` 格式。HACS 通过 GitHub Releases 提供更新。详细信息请参阅[更新日志](../CHANGELOG.md)。

## 兼容性

**Home Assistant 2026.3.0 或更高版本**

### 图例

- ✅ 兼容并已在真实硬件上验证
- ❌ 适配器已提供，等待硬件验证
- ⛔ 待测试

### 微型逆变器

#### TITAN

| 配置 | 型号 | 状态 |
|---|---|---|
| 6-in-1 | **TSOL-MP3000** | ✅ 已验证 |
| 6-in-1 | **TSOL-MP2250, TSOL-MS3000** | ❌ 等待验证 |
| 输入数量待确定 | **MP6000, MP5000, MP4600, MP4000, MP3750, MP3680** | ⛔ 待测试 |

#### GEN3 / GEN3 PLUS — MX 系列

| 配置 | 型号 | 状态 |
|---|---|---|
| 1-in-1 | **MX500** | ✅ 已验证 |
| 1-in-1 | **MX450, MX400** | ❌ 等待验证 |
| 2-in-1 | **MX1000, MX900, MX800** | ❌ 等待验证 |
| 4-in-1 | **MX2250** | ❌ 等待验证 |
| 6-in-1 | **MX3300, MX3000, MX2700, MX2500, MX2400** | ❌ 等待验证 |

#### GEN3 / GEN3 PLUS — MS 系列

| 配置 | 型号 | 状态 |
|---|---|---|
| 1-in-1 | **MS400, MS350, MS300, MS400-D** | ❌ 等待验证 |
| 2-in-1 | **MS800, MS700, MS600, MS600-D, MS800-D** | ❌ 等待验证 |
| 4-in-1 | **MS2000, MS1800, MS1600, MS2000-D, MS3000** | ❌ 等待验证 |

TITAN 的光伏输入可动态检测至 **6 路**。对于 GEN3 / GEN3 PLUS，当前映射覆盖 **1、2 或 4 路光伏输入**；PV5 和 PV6 尚未被检测。

### 其他设备

| 类型 | 型号 | 状态 |
|---|---|---|
| GEN3 PLUS 电池 | **TSOL-DC1000** | ❌ 等待验证 |
| 智能电表 | **TSOL-MG3-MS, DDZY422-D2** | ❌ 等待验证 |

## 安装

### 通过 HACS 安装

[![将 TSUN Local 添加到 HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

也可以手动添加：

1. 在 HACS 中，打开右上角的 **⋮** 菜单，然后选择**自定义存储库**。
2. 添加 `https://github.com/jptstar/tsun-local`，类型选择**集成**。
3. 选择**添加**，然后打开 **TSUN Local**。
4. 选择**下载**并选取最新可用版本。
5. 重新启动 Home Assistant。

如果未显示最新版本，请打开存储库菜单并选择**更新信息**。

### 手动安装

1. 将 `custom_components/tsun_local` 复制到 Home Assistant 的 `/config/custom_components/`。
2. 重新启动 Home Assistant。
3. 打开**设置 → 设备与服务 → 添加集成**。
4. 搜索 **TSUN Local**。
5. 输入 IP 地址、端口以及**微型逆变器铭牌上的 Monitor SN / Logger SN**。

添加设备时，请选择“**搜索本地网络**”或“**手动配置**”，然后为 TSOL-MP3000 选择 **TITAN**，或为 MX500 选择 **GEN3 / GEN3 PLUS**。请输入设备标签上的 **Monitor SN / Logger SN**。搜索仅检查本地 IPv4 网络的 8899 端口，不会向候选地址发送数据。

## 多台设备

可以在同一个 Home Assistant 实例中添加多台兼容的微型逆变器。请为每台设备再次执行**添加集成**，并输入其 IP 地址和唯一 SN。每个配置条目都会创建一台独立设备，拥有自己的实体和通信协调器。

## Home Assistant 设置

在**设置 → 设备与服务 → TSUN Local**中，打开对应设备的菜单：

- **配置**可设置 10 秒至 5 分钟的正常轮询间隔（默认为 30 秒），以及 1 至 60 分钟的离线/夜间轮询间隔（默认为 5 分钟）；
- **重新配置**可修改 IP 地址和 TCP 端口，而不会删除实体；
- 每台设备都有独立的轮询间隔。

## 本地运行与云端隔离

TSUN Local 仅通过本地网络通信，不使用任何云服务。但此集成不会修改设备固件中的云端设置。

如需阻止微型逆变器访问互联网，请在路由器或防火墙中创建规则，阻止其 WAN 访问，同时保留本地网络和 DHCP 访问。Home Assistant 必须仍可通过 TCP 端口 **8899** 访问微型逆变器的 IP 地址。安装完成后，HACS 仅在检查和下载更新时需要互联网连接。

## 夜间运行

当微型逆变器停止供电时，集成会将其标记为离线，而不会在每次轮询时重复记录错误：

- 瞬时测量值（电压、电流、功率和频率）将变为不可用，以避免显示过期数据；
- 每日和总发电量计数器会保留最后一次已知值并继续可用；
- **通信**诊断显示为离线；
- 通信恢复后，连续通信失败计数器会归零；
- 最后一次成功通信时间仍然可用；
- 重试使用已配置的离线/夜间间隔；
- 早晨首次成功响应后恢复正常轮询间隔。

## 传感器

该集成创建一台设备，其中包含交流测量、每个已检测光伏输入的 5 项测量、已检测直流功率之和、4 个诊断传感器以及一个连接状态。

光伏输入数量是动态的：首次读取后 PV1 可用；当检测到有效测量值或发电量计数器时，TITAN 的 PV2 至 PV6 或 GEN3/GEN3 PLUS 的 PV2 至 PV4 会被添加。已检测到的输入会持续保留在 Home Assistant 中。
