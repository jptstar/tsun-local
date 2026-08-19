# MP3000 / TITAN 1511 — field-validation diagnostics

[← Back to the entity reference](ENTITIES.md)

This page documents additional read-only MP3000 / TITAN 1511 diagnostics exposed on the `beta-1097` branch.

> [!IMPORTANT]
> The **names are taken from the TSUN/Talent device profile** and the proposed local addresses have now been **read successfully on a live MP3000**. The decoded values match the TSUN/Talent profile one-to-one. The remaining validation step is a controlled configuration change proving that changing one official setting changes the proposed local register as expected.

All entities below are diagnostics, read-only, and **disabled by default** in Home Assistant.

| Entity key | TSUN/Talent name | Local 1511 register | Decode | Observed MP3000 value | Status |
|---|---|---:|---:|---:|---|
| `grid_qp_voltage_threshold` | QP Voltage Threshold / Seuil de Tension QP | 2048 (`0x0800`) | × 1 V | `105` → 105 V | ✅ Live read confirmed; config-change pending |
| `grid_recovery_rate` | Recovery Rate / Vitesse de récupération | 2003 (`0x07D3`) | × 0.5 s | `1280` → 640.0 s | ✅ Live read confirmed; config-change pending |
| `grid_overvoltage_10min` | Grid Over Voltage 10 Minutes Protection | 2017 (`0x07E1`) | × 0.1 V | `2530` → 253.0 V | ✅ Live read confirmed; config-change pending |
| `grid_overfrequency_reduction_frequency` | Overfrequency Reduction Value / Valeur de Réduction de la Surfréquence | 2030 (`0x07EE`) | × 0.01 Hz | `5020` → 50.20 Hz | ✅ Live read confirmed; config-change pending |
| `grid_overfrequency_reduction_coefficient` | Overfrequency Reduction Coefficient / Coefficient de Réduction de Surfréquence | 2031 (`0x07EF`) | raw | `0x0FA0` / 4000 | ✅ Live read confirmed; config-change pending |
| `overtemperature_protection_temperature` | Overtemperature Protection Value / Valeur de Protection de surtempérature | 2032 (`0x07F0`) | × 1 °C | `79` → 79 °C | ✅ Live read confirmed; config-change pending |
| `grid_start_upper_voltage_limit` | Upper Startup Voltage Limit / Limite Supérieure de Tension de Démarrage | 2043 (`0x07FB`) | × 0.1 V | `2510` → 251.0 V | ✅ Live read confirmed; config-change pending |
| `grid_start_lower_voltage_limit` | Lower Startup Voltage Limit / Limite Inférieure de Tension de Démarrage | 2044 (`0x07FC`) | × 0.1 V | `1960` → 196.0 V | ✅ Live read confirmed; config-change pending |
| `grid_start_upper_frequency_limit` | Upper Startup Frequency Limit / Limite Supérieure de Fréquence de Démarrage | 2045 (`0x07FD`) | × 0.01 Hz | `5009` → 50.09 Hz | ✅ Live read confirmed; config-change pending |
| `grid_start_lower_frequency_limit` | Lower Startup Frequency Limit / Limite Inférieure de Fréquence de Démarrage | 2046 (`0x07FE`) | × 0.01 Hz | `4951` → 49.51 Hz | ✅ Live read confirmed; config-change pending |

## Live PV daily-generation validation

The corrected native-block dump from 2026-08-19 confirms that TSUN Local already uses the correct per-input daily-generation addresses:

| PV | Register | Live value |
|---|---:|---:|
| PV1 | `0x0E15` | 1.04 kWh |
| PV2 | `0x0E1C` | 1.00 kWh |
| PV3 | `0x0E23` | 1.03 kWh |
| PV4 | `0x0EDD` | 1.03 kWh |
| PV5 | `0x0EE4` | 1.03 kWh |
| PV6 | `0x0EEB` | 1.04 kWh |

The six local PV counters sum to **6.17 kWh**. A TSUN Smart screen captured a few minutes earlier showed **6.15 kWh** for daily production, which is consistent with the live local readings.

The separate register `0x0BCE` read **5.55 kWh** at the same time. TSUN Local therefore keeps `ac_energy_today` as the inverter AC/internal daily counter and keeps the six PV daily counters as separate measurements. It is not silently replaced by the PV sum.

The same live dump reports **2164.0 W** as the sum of PV1..PV6 input power and **1959.6 W** on the AC-output register, both from the same MP3000 read.

## Country/profile evidence

The TSUN/Talent device-profile export reports:

- `Réglages du Pays`: **France**
- exported `raw_value`: **1008**
- product: `0_1511_15`
- rated power: 3000 W

The exported value `1008` must **not** be treated as the local country enum itself.

The public TSUN protocol research by **Stefan Allius** in [`s-allius/tsun-gen3-proxy`](https://github.com/s-allius/tsun-gen3-proxy) identified the country/profile field used by the 1097 family and the corresponding country enumeration. In that table, **France is country code `8`**. Stefan's 1097 mapping also associates the country/profile field with local register **`0x1400`**.

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

This 1097 discovery is credited to **Stefan Allius**. TSUN Local reuses that public research for its experimental 1097 support.

### MP3000 / 1511 country candidate

After correcting the expected France value from `1008` to the country enum `8`, the live MP3000 A1/21 dump reveals an exact candidate at the first register of the block:

| TSUN/Talent setting | Expected semantic value | Local 1511 candidate | Live raw value | Status |
|---|---:|---:|---:|---|
| Country / Réglages du Pays = France | `8` | 2000 (`0x07D0`) | `8` (`0x0008`) | ✅ Live device read confirmed; independent validation pending |

The immediately following live values are `0x07D1 = 80` and `0x07D2 = 80`, which also fit the two 40.0 s grid connection/reconnection profile values with a candidate ×0.5 s scaling. This sequence makes `0x07D0` a **very strong 1511 country/profile candidate**, but it is not promoted to fully validated status from a single France device alone.

Changing a grid-country profile solely for reverse-engineering is not required for validation. A safer independent confirmation would be a dump from another MP3000 configured for a different known country, or another authoritative 1511 mapping showing the same field position.

## Evidence level

The evidence is intentionally split into three parts:

1. **Semantic identification:** TSUN/Talent exposes the parameter name and its decoded value for the same MP3000 device.
2. **Live local read:** the proposed A1/21 address is successfully read on the physical MP3000 and decodes to the same value.
3. **Independent validation:** still pending for additional candidate fields. A mapping becomes fully demonstrated when an independent observation distinguishes the field unambiguously, for example a controlled configuration change or a second device/profile with a different known value.

The six PV daily-generation addresses are stronger: they are present in the TSUN Smart 1511 parameter CSV, are read correctly in the native A3/A4 blocks, and their live sum closely matches the TSUN Smart daily-production display.

## Deliberately not mapped yet

`Grid Connection Time` / `Temps de Connexion au Réseau` and `Grid Reconnection Time` / `Temps de Reconnexion au Réseau` now have strong adjacent candidates at `0x07D1` and `0x07D2` (`80 × 0.5 = 40.0 s`), but their individual order cannot be proven while both configured values are identical. They remain candidate mappings until an independent observation distinguishes them.

Likewise, `0x07D0 = 8` matches France according to Stefan Allius's public country table and is now documented as the leading 1511 country/profile candidate, but it remains under independent validation rather than being presented as definitively proven.
