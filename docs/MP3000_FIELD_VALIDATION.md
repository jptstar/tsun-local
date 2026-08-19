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

The TSUN/Talent device profile reports:

- `Réglages du Pays`: **France**
- vendor raw value: **1008**
- product: `0_1511_15`
- rated power: 3000 W

This demonstrates that the cloud/device profile uses a vendor country enumeration rather than the telephone code `33`. No local 1511 register has yet been demonstrated to carry the raw value `1008`, so a `country_profile` entity is **not mapped on protocol 1511** at this stage.

## Evidence level

The evidence is intentionally split into three parts:

1. **Semantic identification:** TSUN/Talent exposes the parameter name and its decoded value for the same MP3000 device.
2. **Live local read:** the proposed A1/21 address is successfully read on the physical MP3000 and decodes to the same value.
3. **Configuration-change validation:** still pending for the ten additional protection fields. A mapping becomes fully demonstrated when changing the official setting changes the proposed local register as expected and restoring it restores the original raw value.

The six PV daily-generation addresses are stronger: they are present in the TSUN Smart 1511 parameter CSV, are read correctly in the native A3/A4 blocks, and their live sum closely matches the TSUN Smart daily-production display.

## Deliberately not mapped yet

`Grid Connection Time` / `Temps de Connexion au Réseau` and `Grid Reconnection Time` / `Temps de Reconnexion au Réseau` are visible in the TSUN/Talent profile, but their local A1/21 addresses cannot yet be identified with sufficient confidence. They remain out of the integration until an address can be demonstrated.

Likewise, the device-profile country value `France / raw 1008` is documented but not assigned to a 1511 local register without direct evidence.
