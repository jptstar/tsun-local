# MP3000 / TITAN 1511 — field-validation diagnostics

[← Back to the entity reference](ENTITIES.md)

This page documents additional read-only MP3000 / TITAN 1511 diagnostics exposed in **TSUN Local 1.5.1-beta.1**.

> [!IMPORTANT]
> The **names are taken from the TSUN/Talent device profile** and the proposed local addresses have been **read successfully on a live MP3000**. The decoded values match the corresponding profile values. For the additional semantic mappings below, the remaining validation step is an independent observation that distinguishes the field unambiguously, normally a controlled configuration change or a second device/profile with a different known value.

All entities below are diagnostics, read-only, and **disabled by default** in Home Assistant.

## Additional A1/21 field-validation entities

| Entity key | TSUN/Talent name | Local 1511 register | Decode | Observed MP3000 value | Status |
|---|---|---:|---:|---:|---|
| `grid_qp_voltage_threshold` | QP Voltage Threshold / Seuil de Tension QP | 2048 (`0x0800`) | × 1 V | `105` → 105 V | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_recovery_rate` | Recovery Rate / Vitesse de récupération | 2003 (`0x07D3`) | × 0.5 s | `1280` → 640.0 s | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_overvoltage_10min` | Grid Over Voltage 10 Minutes Protection | 2017 (`0x07E1`) | × 0.1 V | `2530` → 253.0 V | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_overfrequency_reduction_frequency` | Overfrequency Reduction Value / Valeur de Réduction de la Surfréquence | 2030 (`0x07EE`) | × 0.01 Hz | `5020` → 50.20 Hz | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
| `grid_overfrequency_reduction_coefficient` | Overfrequency Reduction Coefficient / Coefficient de Réduction de Surfréquence | 2031 (`0x07EF`) | raw | `0x0FA0` / 4000 | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |
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

The same dump read the logger RSSI successfully as **30% from `/status.html`**, confirming the logger page-fallback fix used by 1.5.1-beta.1.

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

The TSUN/Talent device-profile export reports:

- `Réglages du Pays`: **France**;
- exported `raw_value`: **1008**;
- product: `0_1511_15`;
- rated power: 3000 W.

The exported value `1008` must **not** be treated as the local country enum itself. The latest live dump provides a direct demonstration of why: at that moment decimal register `3022` (`0x0BCE`) also happened to contain raw `1008`, because the AC daily-energy counter was **10.08 kWh**. Matching an exported value numerically is therefore not sufficient evidence for a country mapping.

### Stefan Allius attribution

Public TSUN protocol research by **Stefan Allius** in [`s-allius/tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy) identified the country/profile field used by the 1097 family and its country enumeration. Stefan's 1097 mapping associates the country/profile field with local register **`0x1400`**.

Country enumeration documented by Stefan Allius:

| Code | Country/profile |
|---:|---|
| 0 | Testing |
| 1 | Brazil |
| 2 | Germany |
| 3 | Netherlands |
| 4 | Ireland |
| 5 | Italy |
| 6 | Poland |
| 7 | Belgium |
| **8** | **France** |
| 9 | Austria |
| 10 | Spain |
| 11 | VDE 0126 |
| 12 | Australia |
| 13 | Thailand MEA |
| 14 | Thailand PEA |
| 15 | South Africa |
| 16 | UK |

This country/profile discovery is credited to **Stefan Allius**. TSUN Local reuses that public research as an external semantic reference for its experimental 1097 support and for the 1511 country-candidate investigation.

### MP3000 / 1511 country candidate

After using the correct semantic France value `8`, the live MP3000 A1/21 block reveals an exact candidate at its first register:

| TSUN/Talent setting | Expected semantic value | Local 1511 candidate | Live raw value | Status |
|---|---:|---:|---:|---|
| Country / Réglages du Pays = France | `8` | 2000 (`0x07D0`) | `8` (`0x0008`) | LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING |

TSUN Local 1.5.1-beta.1 exposes this value only as the raw advanced diagnostic `country_profile_raw`. It does **not** claim that the 1511 semantic address has been fully proven from one France-configured device.

A safer independent confirmation would be a complete dump from another MP3000 configured for a different known country, or another authoritative 1511 mapping showing the same field position.

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

For that reason **1.5.1-beta.1 does not expose two separately named Home Assistant entities for these fields yet**. Their individual semantic order remains pending an independent observation.

## Other strong profile correlations not promoted in beta.1

The full 126-row TSUN/Talent profile also reveals additional numerical correlations in the A1/21 block, including reactive-mode, GFCI/calibration and anti-reflux related fields. They remain research candidates only and are deliberately not promoted to Home Assistant entities in 1.5.1-beta.1.

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
