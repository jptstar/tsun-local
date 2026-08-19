# MP3000 / TITAN — protection entities requiring physical validation

[← Entity reference](ENTITIES.md)

TSUN Local exposes the following MP3000/TITAN protection diagnostics with their **functional names** in Home Assistant.

> [!IMPORTANT]
> The names below come from the MP3000/TITAN parameter export. Their proposed local 1511 register positions and, where applicable, their scaling still require a controlled physical test on real hardware. Home Assistant deliberately shows the clean functional name only; the **validation warning is kept in this documentation**.

The 22 protection fields already present in the official 1511 mobile register asset remain unchanged. The entries below are the additional fields inferred from the gaps and continuation of the same native A1/21 protection block.

| Entity key | Home Assistant name | Talent / MP3000 label | Proposed 1511 register | Proposed scaling | Exported reference value | Status |
|---|---|---|---:|---:|---:|---|
| `grid_qp_voltage_threshold` | QP voltage threshold | Seuil de Tension QP | `0x07D2` | ×0.1 V | 105 V | ⚠️ Physical test required |
| `grid_recovery_speed` | Recovery speed | Vitesse de récupération | `0x07D3` | ×0.1 s | 640.0 s | ⚠️ Physical test required |
| `grid_overtemperature_protection_value` | Overtemperature protection value | Valeur de Protection de surtempérature | `0x07D8` | ×1 °C | 79 °C | ⚠️ Physical test required |
| `grid_overfrequency_reduction_frequency` | Overfrequency reduction value | Valeur de Réduction de la Surfréquence | `0x07E1` | ×0.01 Hz | 50.20 Hz | ⚠️ Physical test required |
| `grid_overfrequency_reduction_coefficient` | Overfrequency reduction coefficient | Coefficient de Réduction de Surfréquence | `0x07EC` | raw | `0FA0` | ⚠️ Physical test required |
| `grid_start_upper_voltage` | Upper start voltage limit | Limite Supérieure de Tension de Démarrage | `0x07F1` | ×0.1 V | 251.00 V | ⚠️ Physical test required |
| `grid_start_lower_voltage` | Lower start voltage limit | Limite Inférieure de Tension de Démarrage | `0x07F2` | ×0.1 V | 196.00 V | ⚠️ Physical test required |
| `grid_start_upper_frequency` | Upper start frequency limit | Limite Supérieure de Fréquence de Démarrage | `0x07F3` | ×0.01 Hz | 50.09 Hz | ⚠️ Physical test required |
| `grid_start_lower_frequency` | Lower start frequency limit | Limite Inférieure de Fréquence de Démarrage | `0x07F4` | ×0.01 Hz | 49.51 Hz | ⚠️ Physical test required |
| `grid_connection_time` | Grid connection time | Temps de Connexion au Réseau | `0x07F7` | ×0.1 s | 40.0 s | ⚠️ Physical test required |
| `grid_reconnection_time` | Grid reconnection time | Temps de Reconnexion au Réseau | `0x07F8` | ×0.1 s | 40.0 s | ⚠️ Physical test required |
| `grid_ten_minute_overvoltage_protection` | 10-minute overvoltage protection | Protection contre la Surtension de 10 Minutes | `0x07F9` | ×0.1 V | 253.00 V | ⚠️ Physical test required |

## Why these positions are candidates

The exported MP3000/TITAN protection sequence aligns with the already mapped 1511 A1/21 protection block:

- `0x07D4`–`0x07D7`, `0x07D9`–`0x07E0`, and `0x07E2`–`0x07EB` are already represented by the official 1511 mobile register asset;
- the export contains additional functional fields exactly where the native address sequence has gaps (`0x07D2`, `0x07D3`, `0x07D8`, `0x07E1`) and then continues after `0x07EB`;
- the later exported sequence is therefore provisionally aligned to `0x07EC`, `0x07F1`–`0x07F4`, and `0x07F7`–`0x07F9`.

This alignment is coherent but **not yet a substitute for a physical register/value comparison**.

## Important correction for `0x07EC`

Earlier TSUN Local development temporarily treated `0x07EC` as a candidate **Power level** by analogy with the adjacent 02B0 protocol layout. The MP3000/TITAN parameter export instead places **Overfrequency reduction coefficient** at this point in the 1511 sequence. The old 1511 Power level candidate has therefore been removed. The new `0x07EC` meaning remains explicitly subject to physical validation.

## Validation target

A candidate can be promoted to validated once a local raw value can be captured from the proposed register and shown to reproduce the MP3000/TITAN exported value with the proposed scaling. Until then, its Home Assistant entity remains read-only, disabled by default, and documented here as requiring a physical check.
