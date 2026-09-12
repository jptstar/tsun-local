# MP3000 / TITAN 1511 — field-validation diagnostics

[← Back to the entity reference](ENTITIES.md)

This page documents additional read-only MP3000 / TITAN 1511 diagnostics exposed in **TSUN Local 1.5.1**.

> [!IMPORTANT]
> The **names are taken from the TSUN/Talent device profile** and the proposed local addresses have been **read successfully on a live MP3000**. The decoded values match the corresponding profile values. For the additional semantic mappings below, the remaining validation step is an independent observation that distinguishes the field unambiguously, normally a controlled configuration change or a second device/profile with a different known value.

All entities below are diagnostics, read-only, and **disabled by default** in Home Assistant.

## Published raw PR #654 field dump

The original MP3000 / 1511 field capture used during the PR #654 investigation is now preserved directly in this repository instead of depending on a GitHub `user-attachments` URL:

- [`tsun_mp3000_1511_pr654_20260816T170853Z.json`](evidence/tsun_mp3000_1511_pr654_20260816T170853Z.json)
- captured: **2026-08-16T17:08:53.109355Z**;
- firmware: **LSW5_SSL_1511_1.03**;
- protocol: **1511 native TITAN**;
- source layout: **s-allius/tsun-gen3-proxy PR #654**;
- acquisition: **read-only**;
- host and logger serial number are absent from the published output;
- SHA-256: `7d44b5c718fee6d03974f345476da8a21831139f90400944b242cf0e80e840cf`.

This file is the original field dump, republished unchanged. It is raw evidence: semantic register labels remain subject to the validation status documented on this page.

## Additional A1/21 field-validation entities

| Entity key | TSUN/Talent name | Local 1511 register | Decode | Observed MP3000 value | Status |
|---|---|---:|---:|---:|---|
| `grid_qp_voltage_threshold` | QP Voltage Threshold / Seuil de Tension QP | 2048 (`0x0800`) | × 1 V | `105` → 105 V | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_recovery_rate` | Recovery Rate / Vitesse de récupération | 2003 (`0x07D3`) | × 0.5 s | `1280` → 640.0 s | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_overvoltage_10min` | Grid Over Voltage 10 Minutes Protection | 2017 (`0x07E1`) | × 0.1 V | `2530` → 253.0 V | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_overfrequency_reduction_frequency` | Overfrequency Reduction Value / Valeur de Réduction de la Surfréquence | 2030 (`0x07EE`) | × 0.01 Hz | `5020` → 50.20 Hz | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_overfrequency_reduction_coefficient` | Overfrequency Reduction Coefficient / Coefficient de Réduction de Surfréquence | 2031 (`0x07EF`) | × 0.01 %/Hz | `0x0FA0` / 4000 → 40.00 %/Hz | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `overtemperature_protection_temperature` | Overtemperature Protection Value / Valeur de Protection de surtempérature | 2032 (`0x07F0`) | × 1 °C | `79` → 79 °C | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_start_upper_voltage_limit` | Upper Startup Voltage Limit / Limite Supérieure de Tension de Démarrage | 2043 (`0x07FB`) | × 0.1 V | `2510` → 251.0 V | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_start_lower_voltage_limit` | Lower Startup Voltage Limit / Limite Inférieure de Tension de Démarrage | 2044 (`0x07FC`) | × 0.1 V | `1960` → 196.0 V | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_start_upper_frequency_limit` | Upper Startup Frequency Limit / Limite Supérieure de Fréquence de Démarrage | 2045 (`0x07FD`) | × 0.01 Hz | `5009` → 50.09 Hz | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_start_lower_frequency_limit` | Lower Startup Frequency Limit / Limite Inférieure de Fréquence de Démarrage | 2046 (`0x07FE`) | × 0.01 Hz | `4951` → 49.51 Hz | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |

## Latest complete native dump

The 2026-08-19 13:31 UTC read-only dump completed every requested native block:

| Native block | Requested | Successful |
|---|---:|---:|
| A1/21 — 2000…2095 | 96 | 96 |
| A1/01 — 3000…3031 | 32 | 32 |
| A2/02 — alarm/status | 4 | 4 |
| A3/03 — PV1…PV3 | 30 | 30 |
| A4/04 — PV4…PV6 | 30 | 30 |

The same dump read the logger RSSI successfully as **30% from `/status.html`**, confirming the logger page-fallback fix used by 1.5.1.

## Live PV daily-generation validation

Native A3/A4 dumps confirm that TSUN Local uses the correct per-input daily-generation positions:

| PV | Register |
|---|---:|
| PV1 | `0x0E15` |
| PV2 | `0x0E1C` |
| PV3 | `0x0E23` |
| PV4 | `0x0EDD` |
| PV5 | `0x0EE4` |
| PV6 | `0x0EEB` |

The separate register `0x0BCE` remains the inverter AC/internal daily counter and is not replaced by the sum of the six PV counters.

## Country/profile evidence

The TSUN/Talent profile export and the independent TSUN Local hardware-dump archive now provide cross-checkable 1511 evidence. The export uses values in the 1000-range while the local A1/21 register uses the compact code itself. Current evidence aligns:

| Local 1511 code | Cloud/profile evidence | Native display name | Local hardware evidence |
|---:|---:|---|---|
| `2` | `1002` | `Deutschland` | cloud/profile evidence; local 1511 dump still requested |
| `6` | `1006` | `Polska` | three independent TSOL-MP3000 dumps |
| `8` | `1008` | `France` | two independent TSOL-MP3000 dumps |

The local source is A1/21 register `2000 / 0x07D0`. Three MP3000 captures from one independent installation read `6`, while the France-configured reference MP3000 and a second independent MP3000 read `8`. This is enough to treat `6 = Polska` and `8 = France` as hardware-supported mappings while keeping code `2 = Deutschland` cloud/profile-backed until a matching local 1511 dump is collected.

TSUN Local therefore exposes two complementary diagnostics: `country_profile_raw` keeps the untouched local integer and `country_profile` shows `code (native name)` when the protocol-specific mapping is known. Unknown 1511 codes remain numeric only. No country/profile write is implemented.

## Grid connection / reconnection pair

Immediately after the country candidate, the same live A1/21 block reads:

```text
0x07D0 = 8
0x07D1 = 80
0x07D2 = 80
0x07D3 = 1280
```

The TSUN/Talent profile contains:

```text
Grid Connection Time      = 40.0 s
Grid Reconnection Time    = 40.0 s
```

With candidate scaling `×0.5 s`, both `0x07D1` and `0x07D2` decode to **40.0 s**. This makes them a strong adjacent candidate pair, but because both official settings currently have the same value the dump cannot prove which register is connection and which is reconnection.

For that reason **1.5.1 does not expose two separately named Home Assistant entities for these fields yet**. Their individual semantic order remains pending an independent observation.

## Other strong profile correlations not promoted in 1.5.1

The full 126-row TSUN/Talent profile also reveals additional numerical correlations in the A1/21 block, including reactive-mode, GFCI/calibration and anti-reflux related fields. They remain research candidates only and are deliberately not promoted to Home Assistant entities in 1.5.1.

## Evidence level

Evidence is intentionally split into three parts:

1. **Semantic identification:** TSUN/Talent exposes the parameter name and decoded value for the same MP3000 device, or a public external mapping supplies a semantic enum such as Stefan Allius's country table.
2. **Live local read:** the proposed A1/21 address is successfully read on the physical MP3000 and decodes to the expected value.
3. **Independent validation:** a mapping becomes fully demonstrated when an independent observation distinguishes the field unambiguously, for example a controlled configuration change or a second device/profile with a different known value.

The six PV daily-generation addresses are stronger because they are present in the TSUN Smart 1511 parameter material, read correctly in the native A3/A4 blocks, and track the live production counters.

## Safety

- All diagnostics are read-only.
- No country/profile write is implemented.
- No grid-protection write is implemented.
- No inverter control command is implemented.
- The diagnostic A1/21 block is read at a slow cadence and a failure does not make normal telemetry fail.
