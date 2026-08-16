# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/).

## [1.4.0-beta.4] - 2026-08-16

### Added

- expose the raw logger inverter profile reported by `inv_tp` as a diagnostic entity;
- expose the logger Wi-Fi signal as a percentage diagnostic entity and refresh it every five minutes independently of inverter polling.

### Fixed

- publish the localized setup and protocol-selector strings under a new beta version so Home Assistant and HACS reload them cleanly.

### Safety

- logger metadata remains read-only and is collected with local HTTP GET requests only;
- no inverter control or configuration write has been added.

## [1.4.0-beta.3] - 2026-08-16

### Added

- firmware-guided protocol selection for logger firmware names containing `1511`, `02B0`, or `1097`;
- a manual **Force protocol probing** mode that deliberately ignores firmware hints and tries the supported adapters, plus direct `1511`, `1097`, and `02B0` choices for controlled compatibility testing;
- diagnostics showing the firmware protocol hint and whether it matches the selected adapter.

### Changed

- automatic network discovery now filters generic port-8899 devices and proposes only candidates whose local logger firmware contains a supported TSUN protocol token;
- 1511 PV inputs are added progressively from observed live or accumulated telemetry instead of assuming six inputs for every TITAN device;
- 1097 PV detection keeps the highest observed input and no longer defaults an all-zero device to six PV inputs;
- manual setup remains available when a logger firmware is unknown or its local web page is unavailable.

### Safety

- discovery and firmware identification use read-only HTTP GET requests only;
- no inverter control or configuration write has been added.

## [1.3.3] - 2026-08-12

### Changed

- republish the HACS release metadata with the generic **TSUN Local** project name;
- align the integration manifest and all localized documentation with version 1.3.3.

## [1.3.2] - 2026-08-12

### Added

- expose the numeric **SN** used for local communication as a translated diagnostic entity alongside the alphanumeric **Micro-inverter SN**.

### Changed

- simplify the device setup documentation in every supported language while retaining the essential automatic discovery, manual fallback, VLAN, and multi-device guidance;
- use the alphanumeric micro-inverter SN as the Home Assistant device serial number while retaining the numeric SN as the stable device-registry identifier;
- keep the logger MAC address as a text diagnostic without registering it as a clickable network connection;
- fix the automatic transition to the next device search so Home Assistant does not display `Invalid flow specified` after adding a discovered micro-inverter.

## [1.3.1] - 2026-08-12

### Added

- expose the alphanumeric micro-inverter serial number from `webdata_sn` as a translated diagnostic entity, separate from the numeric Monitor SN / Logger SN.
- add read-only UDP logger discovery on port 48899, with mandatory TCP validation before a device is proposed;
- add a privacy-safe standalone UDP discovery diagnostic for hardware and routed-network testing.

### Fixed

- read the complete streamed logger status page before parsing metadata;
- use `cover_mid` as the numeric Monitor SN / Logger SN and never confuse it with the inverter serial stored in `webdata_sn`;
- try the unauthenticated status page before the factory HTTP credentials and retain automatic AP-envelope detection as a fallback;
- continue multi-device discovery only after the current config entry has been created, preventing the `already_in_progress` abort shown after adding a device.

### Changed

- network discovery automatically reuses the `/24` subnet of every configured TSUN device, including devices on routed VLANs that are not exposed as Home Assistant adapters.

## [1.3.0] - 2026-08-12

### Added

- setup now detects the Monitor SN / Logger SN automatically from the logger's local `index_cn.html` or `status.html` page;
- logger firmware version and MAC address are exposed as translated diagnostic sensors and added to Home Assistant device information;
- if the page or serial number cannot be read, the same form exposes the Monitor SN field for manual entry.

### Changed

- all README compatibility sections now focus exclusively on TSUN micro-inverters.

### Security

- the factory logger Web credentials are used only for the local detection request and are never stored;
- automatic extraction distinguishes **Device serial number** from the alphanumeric **Inverter serial number**.

## [1.2.1] - 2026-08-11

### Changed

- the connectivity binary sensor is now clearly named **Micro-inverter online** while retaining its stable technical identifier `communication_online`;
- per-device polling now has separate normal, error-retry, and offline/night intervals, defaulting to 20, 20, and 300 seconds;
- the number of consecutive communication failures before offline status is configurable from 1 to 20 and defaults to 3;

### Fixed

- adding a device from network search now automatically starts a fresh search for the next micro-inverter;
- the chained search reuses the same networks and TCP port, excludes the device being saved, and stops when no unconfigured device remains;
- each discovered micro-inverter still creates its own independent Home Assistant config entry and requires its own Monitor SN / Logger SN;
- temporary communication failures retain the latest values until the configured threshold is reached, and a successful response immediately resets the counter.

## [1.2.0] - 2026-08-11

### Added

- protocol-specific inverter alarm polling;
- TITAN/1511 raw global, secondary, and per-PV alarm diagnostics;
- GEN3/GEN3 PLUS/02B0 raw ERR1 to ERR4 diagnostics;
- a global Home Assistant inverter-alarm binary sensor;
- a translated per-device button for an immediate complete manual refresh;
- decimal value, hexadecimal value, and register address for every raw alarm entity;
- translated alarm entities in all eight supported Home Assistant languages;
- tests for alarm requests, protocol-specific entity exposure, raw decoding, and incomplete alarm blocks.
- a privacy-safe Home Assistant diagnostics download with recent protocol transactions;
- a standalone anonymized capture tool for devices that cannot complete setup;
- an offline replay tool for reproducing parser and decoder behavior without the device;
- a guided GitHub form for community compatibility reports.

### Changed

- the global alarm state becomes unavailable when the device is offline or a complete alarm block cannot be read;
- optional alarm reads no longer make the main telemetry update fail;
- compatibility documentation now identifies TSOL-MP3000 and TSOL-MX500 as validated on real hardware;
- the main README is now English, with separate French and German editions;
- compatibility tables distinguish test-ready adapters from models that still require additional register maps;
- setup documentation now reflects automatic protocol detection and no longer asks users to select a device family.
- communication warnings and exported errors no longer include raw network exception text.
- TITAN always exposes the six PV inputs defined by its validated register map, including after a night-time restart;
- polls for multiple configured devices are serialized, and repeated discovery omits devices already configured;
- newly created technical entity IDs explicitly use stable English measurement keys.

### Safety

- raw alarm values are not assigned unverified human-readable fault descriptions;
- no write or control command has been added.
- exported protocol traces exclude the IP address, Monitor SN, and AP envelope.

## [1.1.4] - 2026-08-11

### Added

- automatic local protocol detection;
- the first GEN3 / GEN3 PLUS 02B0 adapter;
- progressive PV-input detection, up to PV6 for TITAN and PV4 for GEN3 / GEN3 PLUS;
- automatic local network search with a manual subnet fallback;
- support for several independently configured micro-inverters;
- configurable normal and offline/night polling intervals;
- Home Assistant translations in English, French, German, Spanish, Italian, Dutch, Polish, and Simplified Chinese;
- privacy-safe protocol diagnostics and unit tests.

### Changed

- daily and total energy counters retain their latest value while the device is offline;
- instantaneous measurements become unavailable while offline;
- total DC power uses only the detected PV inputs;
- the local TCP port defaults to 8899 and remains editable;
- technical entity identifiers remain stable and use English names.

## [1.0.0] - 2026-08-10

### Added

- first public release of TSUN Local;
- stable `tsun_local` Home Assistant domain;
- independent local 1511 implementation for TSOL-MP3000;
- AC and PV1 to PV6 measurements;
- calculated total DC power;
- communication diagnostics and night/offline handling;
- GPL-3.0-or-later licensing and copyright attribution to Jean-Philippe TESTART (jptstar).

[1.4.0-beta.4]: https://github.com/jptstar/tsun-local/releases/tag/v1.4.0-beta.4
[1.4.0-beta.3]: https://github.com/jptstar/tsun-local/releases/tag/v1.4.0-beta.3
[1.3.3]: https://github.com/jptstar/tsun-local/releases/tag/v1.3.3
[1.3.2]: https://github.com/jptstar/tsun-local/releases/tag/v1.3.2
[1.3.1]: https://github.com/jptstar/tsun-local/releases/tag/v1.3.1
[1.3.0]: https://github.com/jptstar/tsun-local/releases/tag/v1.3.0
[1.2.1]: https://github.com/jptstar/tsun-local/releases/tag/v1.2.1
[1.2.0]: https://github.com/jptstar/tsun-local/releases/tag/v1.2.0
[1.1.4]: https://github.com/jptstar/tsun-local/releases/tag/v1.1.4
[1.0.0]: https://github.com/jptstar/tsun-local/releases/tag/v1.0.0
