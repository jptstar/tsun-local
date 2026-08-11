# TSUN Local — Local Home Assistant integration

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Independent TSUN Local icon">
</p>

> **Unofficial project** — This independent community integration is not developed, approved, or maintained by TSUN and is not affiliated with TSUN in any way. TSUN and its product names remain the property of their respective owners. Support requests for this integration must be directed to its author, not to TSUN.

**TSUN Local** integrates compatible TSUN micro-inverters directly into Home Assistant over the local network, without a proxy or cloud service. Version 1.1.1 supports the validated **TSOL-MP3000** and adds initial support for **GEN3**, **GEN3 PLUS**, and other **TITAN** models pending validation on real hardware.

**Author: Jean-Philippe TESTART (jptstar)**

## License

Copyright © 2026 Jean-Philippe TESTART (jptstar).

This project is distributed under the **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`). Modified or redistributed versions must comply with this license and retain the copyright and license notices. See [LICENSE](LICENSE).

The license covers only this independent implementation. It grants no rights to TSUN trademarks, logos, software, or products. This project remains unofficial and unaffiliated with TSUN.

## Versions

Published versions follow `MAJOR.MINOR.PATCH`. HACS uses GitHub Releases to offer updates. See the [changelog](CHANGELOG.md) for details.

## Compatibility

- **Home Assistant 2026.3.0 or later**.

### TITAN micro-inverters

- **TITAN 2250 W–3000 W — MP3000 / MP2250 / MS3000**
  - ✅ **TSOL-MP3000**: compatible and validated on real hardware;
  - ❌ **TSOL-MP2250**: adapter available, not validated on real hardware;
  - ❌ **TSOL-MS3000**: adapter available, not validated on real hardware.
- **TITAN 3680 W–6000 W — MP6000 / MP5000 / MP4600 / MP4000 / MP3750 / MP3680**
  - ❌ not validated and currently unsupported because a complete PV-input map is unavailable.

### GEN3 and GEN3 PLUS micro-inverters

The local adapter is available for devices with 1, 2, or 4 PV inputs. Every model below remains marked ❌ until it is validated with a capture or user feedback from real hardware:

- ❌ **MS300, MS350, MS400, MS400-D**;
- ❌ **MS600, MS700, MS800, MS600-D, MS800-D**;
- ❌ **MS1600, MS1800, MS2000, MS2000-D**;
- ❌ **MS3000**;
- ❌ **MX450, MX500, MX1000**.

The **MX3000** is not declared compatible: the available map ends at PV4 while this model can have more inputs. The **DC1000** storage system and **TSOL-MG3-MS / DDZY422-D2** smart meters are not supported by this micro-inverter adapter.

## Installation

### With HACS

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Or add it manually:

1. In HACS, open the **⋮** menu in the top-right corner, then select **Custom repositories**.
2. Add `https://github.com/jptstar/tsun-local` with type **Integration**.
3. Select **Add**, then open **TSUN Local**.
4. Select **Download** and choose the latest available version.
5. Restart Home Assistant.

If the latest version is not shown, open the repository menu and select **Update information**.

### Manual installation

1. Copy `custom_components/tsun_local` into `/config/custom_components/`.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration**.
4. Search for **TSUN Local**.
5. Enter the IP address, port, and the **SN printed on the micro-inverter label**.

The local protocol is detected automatically when the device is added.

## Multiple devices

Multiple compatible micro-inverters can be added to the same Home Assistant installation. Run **Add integration** for each device and enter its IP address and unique SN. Each entry creates an independent device with its own entities and communication coordinator.

## Home Assistant settings

Under **Settings → Devices & services → TSUN Local**, open the menu for the relevant device:

- **Configure** sets the normal interval from 10 seconds to 5 minutes (30 seconds by default) and the offline/night interval from 1 to 60 minutes (5 minutes by default);
- **Reconfigure** changes the IP address and TCP port without deleting entities;
- each device has independent polling intervals.

## Night operation

When the micro-inverter is no longer powered, the integration marks it offline without repeating an error on every poll:

- instantaneous measurements (voltage, current, power, and frequency) become unavailable so stale values are not displayed;
- daily and total energy counters remain available with their latest known value;
- the **Communication** diagnostic reports offline;
- the consecutive failure counter returns to zero when communication resumes;
- the last successful communication time remains available;
- retries use the configured offline/night interval;
- the configured normal interval is restored after the first successful morning response.

## Sensors

The integration creates one device with AC measurements, 5 measurements for every detected PV input, the sum of detected DC powers, 4 diagnostic sensors, and one connectivity status.

The PV-input count is dynamic: PV1 is available after the first read, then PV2 to PV6 for TITAN or PV2 to PV4 for GEN3/GEN3 PLUS are added when a valid measurement or energy counter is observed. A discovered input remains registered in Home Assistant.
