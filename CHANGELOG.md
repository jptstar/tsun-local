# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/).

## [1.5.1] - 2026-08-19

### Added

- Publish the complete MP3000/1511 alarm interface from 1.5.0: all 224 source positions remain covered without creating 224 permanent Home Assistant entities.
- Keep 12 alarm mappings based on direct physical observations for PV input undervoltage and PV DSP faults across PV1–PV6; all other positions remain neutral until independently confirmed.
- Add a dedicated localized `active_alarm_names` sensor while keeping stable A001–A224 identifiers internal/diagnostic.
- Add ten read-only MP3000/TITAN A1/21 field-validation diagnostics plus the raw 1511 country/profile candidate.
- Add local MP3000 firmware sensors for DSP (`V1.1.72`), QCPU1 (`V1.1.54`) and QCPU2 (`V1.1.54`). FCPU remains intentionally unexposed until a local register is identified.

### Fixed

- Fix logger Wi-Fi RSSI fallback so a valid page without RSSI no longer prevents reading `/status.html`.
- Correct MP3000 `0x07EF` raw `4000` to candidate `40.00 %/Hz` (`×0.01`).
- Remove the discarded MP3000 `output_coefficient_candidate` / Power level candidate entity and clean its beta registry entry.
- Keep unknown user-facing alarm text free of internal Axxx codes while retaining those identifiers for diagnostics.

### Changed

- Keep technical entity IDs stable in English and provide display-name coverage in English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese.
- Refresh the main README, all seven localized READMEs, technical entity reference, public website and visual entity page for the stable 1.5.1 feature set.
- Keep reactive-mode, GFCI, calibration, anti-reflux/zero-export, reduction-signal and insulation correlations in the research backlog only; they are not promoted to semantic Home Assistant entities without independent validation.
- MP3000 maximum presentation with six detected PV inputs is 108 entities: 59 enabled by default and 49 advanced/disabled by default.

### HACS / branding

- Keep HACS metadata aligned with Home Assistant 2026.3.0 or later.
- Verify local `brand/icon.png`, `brand/icon@2x.png`, `brand/logo.png`, `brand/logo@2x.png` assets and keep the website favicon synchronized with the integration icon.

### Safety

- All inverter diagnostics, alarm data and firmware reads remain local and read-only.
- No inverter configuration, protection-setting, country/profile or control write is added.

## [1.5.1-beta.4] - 2026-08-19

### Added

- Add MP3000/1511 DSP, QCPU1 and QCPU2 firmware-version diagnostics from local packed 16-bit words.
- Add the reusable `firmware_version()` decoder for TSUN packed firmware values.

### Changed

- Keep FCPU unexposed until its local 1511 source register is identified.
- Refine the research backlog after a new low-power dump: keep reactive mode, GFCI, K1/K2/K3 and anti-reflux candidates out of semantic entities; promote `0x07ED` to the leading overfrequency-reduction signal candidate; track `0x0BD2` as a dynamic insulation-measurement candidate rather than a fixed 60 MΩ setting.
- Refresh MP3000 documentation to 108 maximum entities, 59 enabled by default and 49 advanced/disabled by default.

### Safety

- All new firmware reads reuse existing local 1511 telemetry blocks and remain read-only.
- No inverter configuration or control write is added.

## [1.5.1-beta.3] - 2026-08-19

### Added

- Add a dedicated MP3000/1511 `active_alarm_names` sensor so localized active alarm text is directly visible and usable.

### Fixed

- Decode MP3000/1511 `0x07EF` raw `4000` with candidate factor `0.01`, exposing `40.00 %/Hz`.
- Keep stable `A001`–`A224` identifiers internal/diagnostic and remove them from user-facing unknown alarm text.
- Refresh web/entity counts to 105 maximum, 56 enabled by default and 49 advanced/disabled by default.
- Remove stale public references to the discarded MP3000 power-level candidate.

### Changed

- Keep technical entity IDs stable in English while display names and alarm text remain localized in all eight supported languages.
- Preserve beta1 logger RSSI/A1/21 diagnostics and beta2 localization/removal fixes.
- Keep newly observed reactive-mode, GFCI, calibration and anti-reflux correlations in the research backlog only.
- Verify HACS metadata and Home Assistant local icon/logo assets.

### Safety

- All MP3000 alarm and diagnostic access remains local and read-only.
- No inverter configuration, protection, country/profile or control write is added.

## [1.5.1-beta.2] - 2026-08-19

### Fixed

- Remove the unvalidated MP3000/1511 `output_coefficient_candidate` entity (`0x07EC`) instead of presenting it as **Power level (candidate)**.
- Use Home Assistant translation keys for the ten 1.5.1 MP3000 field-validation entity names while keeping their technical entity IDs stable in English.
- Enforce complete entity-name coverage in English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese.
- Keep the complete 224-position MP3000 alarm catalogue localized in the same eight languages.
- Remove the discarded candidate from the entity reference and clean the obsolete beta entity from the Home Assistant entity registry on upgrade.

### Safety

- No inverter write or configuration command is added.
- Alarm and diagnostic access remains local and read-only.

## [1.5.1-beta.1] - 2026-08-19

### Added

- Expose ten additional read-only MP3000 / TITAN A1/21 field-validation diagnostics, disabled by default in Home Assistant.
- Expose the raw 1511 country/profile candidate from decimal register `2000` (`0x07D0`); the live France-configured MP3000 reports raw value `8`.
- Document `0x07D1 = 80` and `0x07D2 = 80` as the leading candidate pair for the two 40.0 s grid connection/reconnection settings using a candidate `×0.5 s` scale, without assigning their individual semantic order yet.
- Add beta-release automation for `1.5.1-beta.N` prereleases from the `beta-1097` branch.

### Fixed

- Fix **Logger Wi-Fi signal** remaining unknown when an earlier valid logger page does not contain RSSI; the parser now continues to `/status.html` and other configured status paths until `cover_sta_rssi` is found.
- Stop treating the TSUN/Talent exported country `raw_value` `1008` as the local country enumeration in validation documentation. The live 1511 dump shows that `1008` can independently occur at `0x0BCE` as the AC daily-energy counter.

### Changed

- Keep the complete 1.5.0 MP3000 alarm architecture unchanged: all 224 positions remain covered, the fourteen source words remain optional diagnostics, and no 224-entity wall is created.
- Update the README, entity reference, field-validation documentation and project website while preserving the existing 1.5.0 presentation and layout.
- Explicitly credit **Stefan Allius / `s-allius/tsun-gen3-proxy`** for the public 1097 country/profile research and country enumeration where France is code `8`.
- Keep all new 1511 semantic candidates at evidence status **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING** until independently distinguished.

### Safety

- All added MP3000 diagnostics are local and read-only.
- Logger metadata remains HTTP GET only.
- No inverter configuration, country/profile, grid-protection or control write has been added.

## [1.5.0] - 2026-08-18

### Added

- Add a complete, stable local catalogue for all 224 MP3000 alarm positions exposed by the fourteen 16-bit alarm words.
- Add localized active-alarm names and stable local codes in English, French, German, Dutch, Italian, Spanish, Polish and Simplified Chinese.
- Add an **Active alarms** sensor with the current count and compact active-alarm details.
- Add twelve hardware-validated functional mappings covering low PV input voltage and PV DSP faults for PV1 through PV6.

### Changed

- Keep the remaining 212 alarm positions fully visible with neutral local wording until their functional meaning is physically validated.
- Count the observed MP3000 `8192` position while retaining **Standby — low solar input** as the operating state when it is the only non-fault observation.
- Disable the fourteen complete raw MP3000 alarm-word sensors by default while keeping them available for advanced diagnostics.
- Refresh the README, HACS presentation, entity reference, localized documentation and project website for the 1.5.0 alarm interface.

### Safety

- Alarm decoding is entirely local and read-only.
- No inverter configuration, protection-setting or control write has been added.

## [1.4.1] - 2026-08-17

### Changed

- Rename the user-facing output coefficient to **Power level** across supported protocol families.
- Decode the confirmed 02B0 `0x202C` 1024 full-scale value as a percentage and repair legacy Home Assistant percentage metadata from the temporary raw representation.
- Decode 1511 registers 3017 and 3028 as final inverter and inverter-ambient temperature entities using the `-40 °C` offset, removing the temporary raw 3017/3028 comparison entities.
- Keep 1511 register 3018 raw because its meaning remains unconfirmed.
- Expose 1511 decimal register 2028 (`0x07EC`) as **Power level (candidate)** for field validation.
- Expose the 1097 power-level diagnostic as part of the experimental 1097 mapping.
- Refresh entity documentation, translations and project pages for the new field semantics.

## [1.4.0] - 2026-08-17

### Added

- stable support for the 1511 and 02B0 protocol families, plus experimental 1097 support;
- firmware-guided protocol identification with explicit protocol probing for compatibility testing;
- progressive / dynamic PV-input detection across supported protocol families;
- expanded read-only inverter, logger, alarm and advanced grid-protection diagnostics;
- raw TITAN diagnostic registers 3017, 3018 and 3028 for continued hardware observation;
- a clear 1511 inverter operating-state sensor separating active, standby, observed low-solar standby and fault states;
- eight Home Assistant translation sets and a protocol-oriented entity reference.

### Fixed

- expose all advanced grid-protection timing diagnostics in **seconds** for both 1511 and 02B0, using the existing `0.02` register scaling;
- align the entity reference with the seconds-based timing metadata and remove the provisional unit/scaling markers;
- correct 1511 per-PV daily-energy register offsets and use the corrected positions for PV detection;
- keep optional TITAN raw register 3018 from breaking devices or fixtures where that register is absent;
- preserve logger metadata and device discovery state across temporary communication failures;
- migrate beta-era automatic grid-timing display units from `ms` to `s` while preserving explicit user unit choices;
- stop treating the MP3000-observed `0x2000` / `8192` low-solar status bit as a fault by itself while preserving the raw alarm word;
- stop presenting the unconfirmed 02B0 `0x202C` output-coefficient encoding as a percentage.

### Changed

- advanced diagnostics remain disabled by default so normal Home Assistant device pages stay uncluttered;
- TITAN registers 3017 and 3028 remain unscaled raw decimal measurement sensors so their Home Assistant history can be charted during temperature-mapping validation; no temperature offset is applied yet;
- version 1.4 moves TSUN Local from individual known models toward protocol-family compatibility;
- the experimental 1097 implementation continues to credit the public `s-allius/tsun-gen3-proxy` protocol research by Stefan Allius.

### Safety

- all inverter access remains read-only;
- no inverter configuration, protection-setting or control write has been added;
- no cloud or proxy is required in the local Home Assistant data path.

## [1.4.0-beta.8] - 2026-08-17

### Added

- complete read-only advanced grid-protection diagnostics for the 1511 and 02B0 protocol families;
- read-only 02B0 output coefficient diagnostic;
- experimental 1097 diagnostics for protocol/inverter versions, inverter temperature, insulation impedance RX/RY and raw country/profile code;
- advanced diagnostic entity names in English, French, German, Dutch, Italian, Spanish, Polish and Simplified Chinese;
- a concise 1.4-ready README focused on local access and protocol-family compatibility.

### Fixed

- correct 1511 per-PV daily-energy register offsets from `base + 4` to `base + 5` for PV1 through PV6;
- use the corrected daily-energy positions when detecting populated 1511 PV inputs.

### Changed

- advanced diagnostics are categorized as diagnostic entities and disabled by default so normal installations stay uncluttered;
- the experimental 1097 diagnostics continue to credit the public `s-allius/tsun-gen3-proxy` protocol research by Stefan Allius.

### Safety

- all newly added diagnostics are read-only;
- the 02B0 output coefficient is read but never written;
- no inverter configuration or control write has been added.

## [1.4.0-beta.7] - 2026-08-16

### Added

- firmware-guided automatic protocol selection using the protocol identifier reported by the TSUN logger firmware;
- experimental 1097 protocol adapter and explicit forced protocol probing for compatibility testing;
- automatic filtering of network discovery results using supported firmware protocol identifiers;
- progressive PV-input detection based on actual device telemetry;
- logger Wi-Fi signal diagnostic with an independent five-minute refresh;
- raw logger inverter profile in Home Assistant device information;
- read-only access to the TITAN native A1/21 diagnostic block (decimal registers 2000-2095), collected at a slow diagnostic cadence;
- cross-protocol diagnostic entities for raw inverter status, rated inverter power and maximum designed power on 1511, 02B0 and 1097;
- read-only slow diagnostic reads for 02B0 register `0x2007` and 1097 register `0x1437`;
- raw diagnostic entities for TITAN registers 3017 and 3028, whose physical meaning and scaling remain unconfirmed.

### Changed

- automatic protocol selection is now driven by the firmware token instead of guessing from inverter characteristics;
- detected PV inputs are retained and never removed after discovery;
- logger metadata refresh is independent from inverter telemetry polling and freshly retrieved metadata is preserved across later inverter polling failures;
- raw logger profile discovery is retried until available and the profile is stored as the Home Assistant device model identifier;
- registers 3017 and 3028 are exposed without an offset, temperature unit, or temperature device class, and their entity names explicitly state that their meaning is unconfirmed;
- optional inverter diagnostic blocks are read on the first poll and then refreshed every five minutes;
- credit to Stefan Allius and the public `s-allius/tsun-gen3-proxy` research is retained for the experimental 1097 protocol work.

### Fixed

- remove the obsolete **Raw logger profile** diagnostic entity left in the Home Assistant entity registry by earlier beta releases;
- remove the unused raw-profile entity translation key;
- preserve logger metadata correctly across failed inverter polls.

## [1.4.0-beta.6] - 2026-08-16

### Fixed

- remove the obsolete **Raw logger profile** diagnostic entity left in the Home Assistant entity registry by beta.4; the raw profile is now shown only in device information as the model identifier;
- remove the unused raw-profile entity translation key from every supported language.

## [1.4.0-beta.5] - 2026-08-16

### Fixed

- refresh logger Wi-Fi signal with a true independent five-minute timer, including while inverter TCP polling is offline;
- preserve freshly refreshed logger metadata when a subsequent inverter poll fails;
- retry raw logger profile discovery every five minutes until it becomes available, then update Home Assistant device information immediately;
- include the raw logger profile in entity `DeviceInfo` so normal entity registration also carries the profile into the device registry.

### Changed

- credit Stefan Allius and the public `s-allius/tsun-gen3-proxy` research directly in the experimental 1097 protocol source.

## [1.4.0-beta.4] - 2026-08-16

### Added

- show the raw logger inverter profile reported by `inv_tp` in Home Assistant device information;
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
- 1097 PV detection keeps the highest observed input and no longer defaults an all-zero device to six active PV inputs;
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

[1.5.1-beta.1]: https://github.com/jptstar/tsun-local/releases/tag/v1.5.1-beta.1
[1.5.0]: https://github.com/jptstar/tsun-local/releases/tag/v1.5.0
[1.4.1]: https://github.com/jptstar/tsun-local/releases/tag/v1.4.1
[1.4.0]: https://github.com/jptstar/tsun-local/releases/tag/v1.4.0
[1.4.0-beta.8]: https://github.com/jptstar/tsun-local/releases/tag/v1.4.0-beta.8
[1.4.0-beta.7]: https://github.com/jptstar/tsun-local/releases/tag/v1.4.0-beta.7
[1.4.0-beta.6]: https://github.com/jptstar/tsun-local/releases/tag/v1.4.0-beta.6
[1.4.0-beta.5]: https://github.com/jptstar/tsun-local/releases/tag/v1.4.0-beta.5
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
