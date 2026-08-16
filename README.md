# TSUN Local — Local Home Assistant integration

[English](README.md) | [Français](docs/README_FR.md) | [Deutsch](docs/README_DE.md) | [Nederlands](docs/README_NL.md) | [Italiano](docs/README_IT.md) | [Español](docs/README_ES.md) | [Polski](docs/README_PL.md) | [简体中文](docs/README_ZH.md)

[![GitHub Release](https://img.shields.io/github/v/release/jptstar/tsun-local)](https://github.com/jptstar/tsun-local/releases)

<p align="center">
  <img src="https://raw.githubusercontent.com/jptstar/tsun-local/main/custom_components/tsun_local/brand/icon@2x.png" width="160" alt="Independent TSUN Local icon">
</p>

> **Unofficial project** — This independent community integration is not developed, approved, or maintained by TSUN and is not affiliated with TSUN in any way. TSUN and its product names remain the property of their respective owners. Support requests for this integration must be directed to its author, not to TSUN.

**TSUN Local** connects compatible TSUN micro-inverters directly to Home Assistant over the local network, without a proxy or cloud service. Version **1.4.0-beta.6** supports the **TSOL-MP3000** and **TSOL-MX500**, both validated on real hardware, and provides test-ready adapters for other TITAN, GEN3, and GEN3 PLUS models.

## About this project

I originally developed this integration for fun and for my own Home Assistant installation. Because many owners have difficulty accessing their TSUN micro-inverters locally, I am making it available so others can benefit from it as well.

Hardware feedback, diagnostic results, and focused bug reports are welcome. I can spend some time improving compatibility when users provide useful information, but this remains a personal hobby rather than my main activity, so replies and fixes may sometimes take time.

## Main features

- fully local polling over TCP, with no proxy and no cloud dependency;
- automatic selection between the currently supported local protocol adapters;
- combined native UDP discovery and bounded TCP network scanning;
- automatic detection of the available PV inputs within the validated register maps;
- AC voltage, current, frequency, power, daily energy, and total energy;
- voltage, current, power, daily energy, and total energy for every detected PV input;
- total DC power calculated from the detected PV powers;
- raw inverter alarms and a global alarm status;
- communication diagnostics with separate normal, error-retry, and offline/night polling intervals;
- a per-device button for an immediate manual data refresh;
- multiple micro-inverters in the same Home Assistant installation;
- translated Home Assistant entities in English, French, German, Spanish, Italian, Dutch, Polish, and Simplified Chinese.

## Compatibility

- **Home Assistant 2026.3.0 or later**.

**Legend:** ✅ validated on real hardware · 🧪 adapter ready for community testing · 🔎 additional register information or hardware captures required · ⏸️ currently out of scope.

### TITAN micro-inverters

| PV inputs | Models | Status | Notes |
|---:|---|:---:|---|
| 6 | **TSOL-MP3000** | ✅ | Validated on real hardware |
| 6 | TSOL-MP2250, TSOL-MS3000 | 🧪 | 1511 adapter ready for testing |
| 6 | MP3680, MP3750, MP4000, MP4600, MP5000, MP6000 | 🔎 | Six-input hardware; local protocol and register map still require a hardware capture |

### GEN3 and GEN3 PLUS micro-inverters

| PV inputs | Models | Status | Notes |
|---:|---|:---:|---|
| 1 | **TSOL-MX500** | ✅ | Validated on real hardware |
| 1 | MX400, MX450, MS300, MS350, MS400, MS400-D | 🧪 | 02B0 adapter ready for testing |
| 2 | MX800, MX900, MX1000, MS600, MS700, MS800, MS600-D, MS700-D, MS800-D | 🧪 | 02B0 adapter ready for testing |
| 4 | MX2250, MS1600, MS1800, MS2000, MS2000-D | 🧪 | 02B0 adapter ready for testing |
| 6 | MS3000, MX2400, MX2500, MX2700, MX3000/MX3000D, MX3300 | 🔎 | The available 02B0 map currently ends at PV4 |

## Installation

### With HACS

[![Add TSUN Local to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jptstar&repository=tsun-local&category=integration)

Or add it manually:

1. In HACS, open the **⋮** menu and select **Custom repositories**.
2. Add `https://github.com/jptstar/tsun-local` with type **Integration**.
3. Open **TSUN Local**, select **Download**, and choose the latest release.
4. Restart Home Assistant.

If a new release does not appear, open the repository menu and select **Update information**.

### Manual installation

1. Copy `custom_components/tsun_local` into `/config/custom_components/`.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration**.
4. Search for **TSUN Local**.

## Adding a device

TSUN Local can search for micro-inverters on the local network, or you can enter their IP address manually. TCP port `8899` is proposed by default and remains editable.

The local protocol and numeric **SN** are detected automatically. If necessary, the SN can be entered manually from the local status page or the device label. It is distinct from the alphanumeric **Micro-inverter SN**.

If a device is on another VLAN and is not found, enter its subnet in CIDR notation or use manual configuration.

Multiple micro-inverters can be added. Each device has its own entities and polling settings.

## Polling settings

Under **Settings → Devices & services → TSUN Local**, open **Configure** for the relevant device:

- normal polling interval: 10 seconds to 5 minutes, 20 seconds by default;
- retry interval after a communication error: 10 seconds to 5 minutes, 20 seconds by default;
- offline/night polling interval: 1 to 60 minutes, 5 minutes by default;
- consecutive failures before the device goes offline: 1 to 20, 3 by default.

Use **Reconfigure** to change the IP address or TCP port without deleting the existing entities.

The **Refresh data** button runs one immediate complete poll of its micro-inverter without changing the configured intervals. If another TSUN device is being read, the manual refresh waits for that poll to finish.

## Entities

The integration creates one Home Assistant device for each configured micro-inverter. Technical entity identifiers remain in English, while their displayed names are translated.

New identifiers use stable English keys such as `ac_power`, `pv1_current`, and `pv1_energy_total`. An identifier already stored by Home Assistant from an older release is deliberately not renamed automatically because that could break dashboards and automations; it can be changed manually from the entity settings if desired.

Available data includes:

- AC instantaneous measurements and energy counters;
- five measurements for every detected PV input;
- calculated total DC power;
- four communication diagnostics, plus **SN**, **Micro-inverter SN**, logger firmware, and MAC-address diagnostic sensors;
- a **Micro-inverter online** connectivity binary sensor;
- a global inverter alarm status and protocol-specific raw alarm registers;
- a manual **Refresh data** button.

PV detection is progressive. TITAN can expose PV1 to PV6 with the current 1511 map. GEN3/GEN3 PLUS can expose PV1 to PV4 with the current 02B0 map. Once an input is discovered, its entities remain registered in Home Assistant.

### Inverter alarms

Alarm information is read separately from communication failures:

- TITAN/1511 exposes four global alarm words, four secondary words, and one raw alarm word for every detected PV input;
- GEN3/GEN3 PLUS/02B0 exposes the four raw ERR1 to ERR4 registers;
- every raw diagnostic shows its decimal value, hexadecimal value, and register address;
- any non-zero raw value turns on the global **Inverter alarm** binary sensor;
- if the complete alarm block cannot be read, the global alarm state becomes unavailable instead of reporting a false clear state.

Published manuals describe fault categories, but no public document found so far defines a reliable register/bit mapping for every supported family. TSUN Local therefore keeps unknown values raw instead of displaying an unverified fault description.

The documented categories include abnormal PV voltage or current, missing or abnormal grid voltage/frequency, overheating, ground-fault or insulation faults, and internal inverter faults. These categories are informative only until their relationship with each raw register has been confirmed.

## Night and offline operation

When a solar-powered micro-inverter stops answering at night:

Until the configurable failure threshold is reached, the latest values remain available and retries use the error interval. When the threshold is reached (3 failures by default), the device goes offline and uses the offline/night interval. The first successful response immediately resets the counter to zero and restores normal polling.

- instantaneous voltage, current, power, and frequency become unavailable;
- alarm status and raw alarm registers become unavailable;
- daily and total energy counters retain their last known value;
- **Micro-inverter online** turns off and the failure counter increases;
- the slower offline/night interval is used;
- normal polling resumes after the first successful response.

## Local operation and cloud access

TSUN Local itself does not contact a TSUN cloud service. Once installed, its telemetry is read directly from the local device.

The integration does not disable the micro-inverter’s own internet or cloud communication. If complete internet isolation is required, it must be configured on the router or firewall while preserving local access from Home Assistant to the device’s IP address and TCP port.

## Community testing and diagnostics

Models marked 🧪 are genuinely ready to be tried. Successful tests and failed attempts are both useful: differences between models or firmware versions can only be confirmed with real-hardware feedback.

If the integration is already configured:

1. Open **Settings → Devices & services → TSUN Local**.
2. Enable debug logging from the integration menu, reproduce the problem once, then disable debug logging.
3. Download the integration diagnostics from the same integration or device page.
4. Open a [compatibility report](https://github.com/jptstar/tsun-local/issues/new/choose) with the exact model, firmware version, TSUN Local version, and the downloaded file.

If setup cannot complete, run the standalone capture from a copy of this repository:

```bash
python3 tools/diagnose_device.py --host DEVICE_IP
```

The numeric SN is requested interactively and is not stored in the command history. The generated `tsun_local_diagnostic.json` contains decoded measurements and a short circular trace of inner protocol requests and responses. It does **not** contain the device IP address, SN, logger MAC address, or AP envelope. Review the file before sharing it, as production and energy readings remain visible.

The captured responses can be replayed locally without the physical device:

```bash
python3 tools/replay_diagnostic.py tsun_local_diagnostic.json
```

Available register maps provide a solid starting point, but they cannot guarantee that every untested model or firmware behaves identically. This capture-and-replay path makes focused compatibility fixes possible without remote access to another user’s network.

## Possible next additions

The following ideas are deliberately not enabled yet and require validation before implementation:

- grid-protection thresholds in read-only diagnostic entities;
- the 02B0 output coefficient as a read-only percentage;
- Home Assistant notifications or repairs for persistent inverter alarms;
- translated fault descriptions after the raw register/bit mapping has been confirmed;
- additional local protocol adapters for future TSUN micro-inverter families.

No control or write command will be added without explicit safeguards and real-hardware validation.

## Author

Jean-Philippe TESTART (`jptstar`)


## Acknowledgements

The 1097 register mapping was informed by publicly available protocol research
from the `s-allius/tsun-gen3-proxy` project by Stefan Allius.

## License

Copyright © 2026 Jean-Philippe TESTART (jptstar).

This project is distributed under the **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`). Modified or redistributed versions must comply with this license and retain the copyright and license notices. See [LICENSE](LICENSE).

The license covers only this independent implementation. It grants no rights to TSUN trademarks, logos, software, or products. This project remains unofficial and unaffiliated with TSUN.
