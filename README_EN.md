# TSUN Local — Local Home Assistant integration

[Français](README.md) | [English](README_EN.md) | [Deutsch](README_DE.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Independent TSUN Local icon">
</p>

> **Unofficial project** — This independent community integration is not developed, approved, or maintained by TSUN and is not affiliated with TSUN in any way. TSUN and its product names remain the property of their respective owners. Support requests for this integration must be directed to its author, not to TSUN.

**TSUN Local** integrates TSUN TITAN micro-inverters directly into Home Assistant over the local network, without a proxy or cloud service. The current version supports the **TSOL-MP3000**.

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

- [**TITAN 2250 W–3000 W — MP3000 / MP2250 / MS3000**](https://fr.tsun-ess.com/titan-microinverter_4/titan-microinverter-2250w-3000w.html)
  - ✅ **TSOL-MP3000**: compatible and validated on real hardware, with 6 PV inputs;
  - ❌ **TSOL-MP2250**: untested; compatibility must be confirmed through user feedback;
  - ❌ **TSOL-MS3000**: untested; compatibility must be confirmed through user feedback.
- [**TITAN 3680 W–6000 W — MP6000 / MP5000 / MP4600 / MP4000 / MP3750 / MP3680**](https://fr.tsun-ess.com/titan-microinverter_4/titan-microinverter-3680w-6000w.html)
  - ❌ **TSOL-MP6000**: untested; compatibility must be confirmed through user feedback;
  - ❌ **TSOL-MP5000**: untested; compatibility must be confirmed through user feedback;
  - ❌ **TSOL-MP4600**: untested; compatibility must be confirmed through user feedback;
  - ❌ **TSOL-MP4000**: untested; compatibility must be confirmed through user feedback;
  - ❌ **TSOL-MP3750**: untested; compatibility must be confirmed through user feedback;
  - ❌ **TSOL-MP3680**: untested; compatibility must be confirmed through user feedback.

## Installation

### With HACS

1. In HACS, open **Integrations**, then **Custom repositories**.
2. Add `https://github.com/jptstar/tsun-local` with type **Integration**.
3. Install **TSUN Local**, then restart Home Assistant.

### Manual installation

1. Copy `custom_components/tsun_local` into `/config/custom_components/`.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration**.
4. Search for **TSUN Local**.
5. Enter the IP address, port, and the **SN printed on the micro-inverter label**.

## Multiple devices

Multiple compatible micro-inverters can be added to the same Home Assistant installation. Run **Add integration** for each device and enter its IP address and unique SN. Each entry creates an independent device with its own entities and communication coordinator.

## Home Assistant settings

Under **Settings → Devices & services → TSUN Local**, open the menu for the relevant device:

- **Configure** sets the normal interval from 10 seconds to 5 minutes (30 seconds by default) and the offline/night interval from 1 to 60 minutes (5 minutes by default);
- **Reconfigure** changes the IP address and TCP port without deleting entities;
- each device has independent polling intervals.

## Night operation

When the micro-inverter is no longer powered, the integration marks it offline without repeating an error on every poll:

- AC/PV measurements become unavailable so stale values are not displayed;
- the **Communication** diagnostic reports offline;
- the consecutive failure counter returns to zero when communication resumes;
- the last successful communication time remains available;
- retries use the configured offline/night interval;
- the configured normal interval is restored after the first successful morning response.

## Sensors

**TITAN:** the integration creates one device with AC measurements, 5 measurements for each of the 6 PV inputs, the sum of the 6 DC powers, 4 diagnostic sensors, and one connectivity status.
