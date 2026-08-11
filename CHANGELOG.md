# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/).

## [1.1.7] - 2026-08-11

### Changed

- device setup and network discovery no longer ask the user to choose **TITAN** or **GEN3 / GEN3 PLUS**;
- the integration now tries the supported read-only local protocol adapters automatically after the Monitor SN / Logger SN is entered, then stores the protocol that responds correctly;
- reconfiguration retains the detected protocol automatically;
- setup descriptions and documentation were updated in all eight supported languages.

### Added

- a unit test verifying that automatic detection tries the next adapter after a failure and reuses the successful adapter for subsequent reads.

## [1.1.6] - 2026-08-11

### Fixed

- automatic discovery now scans every active IPv4 network exposed by Home Assistant instead of only the single network selected for mDNS;
- when no device is found automatically, the setup flow now allows a routed LAN or VLAN subnet and port to be entered manually in CIDR notation;
- discovery uses a more tolerant connection timeout while keeping the scan limited to at most 254 addresses per subnet.

### Added

- unit tests for bounded adapter networks, invalid oversized discovery networks, and ignored loopback interfaces.

## [1.1.5] - 2026-08-11

### Changed

- clarified that TSUN Local is a personal integration developed as a hobby and shared with the community;
- clarified support expectations: feedback and diagnostics can help improve support for specific models, but replies and fixes may take time;
- kept the English documentation at the repository root for GitHub and HACS, with the seven translations grouped in the `docs/` directory;
- renamed the ⛔ status to “To be tested” in every language.

## [1.1.4] - 2026-08-11

### Added

- on-demand discovery of candidate devices on the local IPv4 network, without sending data during detection;
- explicit selection of the **TITAN** or **GEN3 / GEN3 PLUS** family during setup and reconfiguration;
- detailed 02B0 protocol diagnostics with Monitor SN / Logger SN masking;
- a standalone diagnostic tool to facilitate validation on real hardware.

### Changed

- declared **MX500** compatible and validated on real hardware with one PV input;
- restructured the MX and MS compatibility matrix according to models with 1, 2, 4, or 6 PV inputs;
- added **TSOL-DC1000** as a GEN3 PLUS battery pending validation;
- classified **TSOL-MG3-MS** and **DDZY422-D2** as smart meters pending validation, without assigning a protocol;
- made the English documentation the main README and moved the French documentation to `README_FR.md`;
- clarified in configuration labels that the **Monitor SN / Logger SN** is printed on the device label;
- documented fully local operation and optional cloud isolation at the router or firewall level.

### Fixed

- GEN3 / GEN3 PLUS device setup now uses its adapter directly instead of trying another protocol family first.

## [1.1.3] - 2026-08-11

### Added

- complete documentation in Dutch, Italian, Spanish, Polish, and Simplified Chinese.

### Changed

- added a shared eight-language selector to every README.

## [1.1.2] - 2026-08-11

### Added

- Home Assistant translations in Dutch (`nl`), Italian (`it`), Spanish (`es`), Polish (`pl`), and Simplified Chinese (`zh-Hans`).

## [1.1.1] - 2026-08-11

### Changed

- added **MX500** to the list of GEN3 / GEN3 PLUS micro-inverters available for testing and awaiting validation on real hardware.

## [1.1.0] - 2026-08-11

### Added

- automatic local protocol detection when adding a device;
- the first GEN3 / GEN3 PLUS adapter based on the provided 02B0 register map;
- progressive PV-input discovery: up to 6 inputs for TITAN and up to 4 inputs for GEN3 / GEN3 PLUS;
- dynamic creation in Home Assistant of entities corresponding to detected PV inputs;
- unit tests for AP envelopes, CRC, requests, responses, 32-bit counters, and both protocol decoders.

### Changed

- total DC power now sums only detected PV inputs;
- energy counters remain available while offline and at night, while instantaneous measurements become unavailable;
- compatibility documentation now distinguishes validated devices, devices available for testing, and unsupported devices.

## [1.0.1] - 2026-08-11

### Changed

- the default local port `8899` is now pre-filled in the Home Assistant form and remains user-configurable.

## [1.0.0] - 2026-08-10

### Added

- first public release of TSUN Local;
- the generic and stable Home Assistant domain `tsun_local`;
- a shared interface for extensible protocol adapters;
- the first independent implementation of the local 1511 protocol for the TSOL-MP3000;
- AC and PV1–PV6 readings;
- total DC power calculated as the sum of the six PV powers;
- communication diagnostics and automatic night-time operation handling;
- configurable normal and offline/night polling intervals for each device;
- support for multiple micro-inverters;
- configuration and reconfiguration from Home Assistant;
- Home Assistant translations in French, English, and German;
- GitHub documentation in French, English, and German;
- the GPL-3.0 license and copyright notice for Jean-Philippe TESTART (jptstar).

[1.1.7]: https://github.com/jptstar/tsun-local/compare/v1.1.6...v1.1.7
[1.1.6]: https://github.com/jptstar/tsun-local/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/jptstar/tsun-local/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/jptstar/tsun-local/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/jptstar/tsun-local/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/jptstar/tsun-local/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/jptstar/tsun-local/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/jptstar/tsun-local/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/jptstar/tsun-local/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/jptstar/tsun-local/releases/tag/v1.0.0
