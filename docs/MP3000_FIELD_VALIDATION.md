# MP3000 / TITAN 1511 — field-validation diagnostics

[← Back to the entity reference](ENTITIES.md)

This page documents additional read-only MP3000 / TITAN 1511 diagnostics that are exposed on the `beta-1097` branch for field testing.

> [!WARNING]
> The **names are taken from the TSUN/Talent device profile** and the proposed local addresses are supported by a one-to-one value correlation with a real MP3000 A1/21 register dump. The local register-to-name association has **not yet been confirmed by changing the corresponding setting or deliberately triggering the physical condition on hardware**. These entities therefore require a physical validation test before they can be described as confirmed mappings.

All entities below are diagnostics, read-only, and **disabled by default** in Home Assistant.

| Entity key | TSUN/Talent name | Local 1511 register | Decode | Observed MP3000 value | Status |
|---|---|---:|---:|---:|---|
| `grid_qp_voltage_threshold` | QP Voltage Threshold / Seuil de Tension QP | 2048 (`0x0800`) | × 1 V | `105` → 105 V | 🧪 Physical test required |
| `grid_recovery_rate` | Recovery Rate / Vitesse de récupération | 2003 (`0x07D3`) | × 0.5 s | `1280` → 640.0 s | 🧪 Physical test required |
| `grid_overvoltage_10min` | Grid Over Voltage 10 Minutes Protection | 2017 (`0x07E1`) | × 0.1 V | `2530` → 253.0 V | 🧪 Physical test required |
| `grid_overfrequency_reduction_frequency` | Overfrequency Reduction Value / Valeur de Réduction de la Surfréquence | 2030 (`0x07EE`) | × 0.01 Hz | `5020` → 50.20 Hz | 🧪 Physical test required |
| `grid_overfrequency_reduction_coefficient` | Overfrequency Reduction Coefficient / Coefficient de Réduction de Surfréquence | 2031 (`0x07EF`) | raw | `0x0FA0` / 4000 | 🧪 Physical test required |
| `overtemperature_protection_temperature` | Overtemperature Protection Value / Valeur de Protection de surtempérature | 2032 (`0x07F0`) | × 1 °C | `79` → 79 °C | 🧪 Physical test required |
| `grid_start_upper_voltage_limit` | Upper Startup Voltage Limit / Limite Supérieure de Tension de Démarrage | 2043 (`0x07FB`) | × 0.1 V | `2510` → 251.0 V | 🧪 Physical test required |
| `grid_start_lower_voltage_limit` | Lower Startup Voltage Limit / Limite Inférieure de Tension de Démarrage | 2044 (`0x07FC`) | × 0.1 V | `1960` → 196.0 V | 🧪 Physical test required |
| `grid_start_upper_frequency_limit` | Upper Startup Frequency Limit / Limite Supérieure de Fréquence de Démarrage | 2045 (`0x07FD`) | × 0.01 Hz | `5009` → 50.09 Hz | 🧪 Physical test required |
| `grid_start_lower_frequency_limit` | Lower Startup Frequency Limit / Limite Inférieure de Fréquence de Démarrage | 2046 (`0x07FE`) | × 0.01 Hz | `4951` → 49.51 Hz | 🧪 Physical test required |

## Evidence level

The evidence is intentionally split into two parts:

1. **Semantic identification:** TSUN/Talent exposes the parameter name and its decoded value for the same MP3000 device.
2. **Local address correlation:** the local A1/21 dump contains a raw register whose decoded value exactly matches that TSUN/Talent value.

That correlation is strong enough to expose the values for beta testing, but it is not equivalent to a controlled hardware validation. A field becomes **validated** only after a physical or configuration test demonstrates that changing or triggering that parameter changes the proposed local register as expected.

## Deliberately not mapped yet

`Grid Connection Time` / `Temps de Connexion au Réseau` and `Grid Reconnection Time` / `Temps de Reconnexion au Réseau` are visible in the TSUN/Talent profile, but their local A1/21 addresses cannot yet be identified with sufficient confidence from the current static dump. They remain out of the integration until an address can be demonstrated.
