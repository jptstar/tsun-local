# TSUN Local — Entity reference

[← Back to the main README](../README.md)

This page lists the Home Assistant entities exposed by TSUN Local **by local protocol family**.

> [!NOTE]
> The exact number of entities depends on the protocol, the number of PV inputs detected on the device, and the data actually returned by the inverter. Home Assistant may add a device prefix to the final `entity_id`; the stable TSUN Local object-id suffix is shown below.

## Legend

| Mark | Meaning |
|---|---|
| ✅ | Enabled by default |
| 🛡️ | Advanced diagnostic entity, **disabled by default** |
| 🔄 | Created dynamically when the corresponding PV input is detected |
| 🧪 | Experimental protocol support |

---

## Common entities — 1511 · 02B0 · 1097

These entities are available across all three supported protocol families.

### AC / production sensors

| Entity key | Home Assistant name | Unit | Default |
|---|---|---:|:---:|
| `ac_voltage` | AC voltage | V | ✅ |
| `ac_current` | AC current | A | ✅ |
| `ac_frequency` | AC frequency | Hz | ✅ |
| `ac_power` | AC power | W | ✅ |
| `ac_energy_today` | AC energy today | kWh | ✅ |
| `ac_energy_total` | Total AC energy | kWh | ✅ |
| `dc_power_total` | Total DC power | W | ✅ |

### Device / logger diagnostics

| Entity key | Home Assistant name | Unit / type | Default |
|---|---|---|:---:|
| `inverter_status_raw` | Raw inverter status | raw | ✅ |
| `rated_power` | Rated inverter power | W | ✅ |
| `max_designed_power` | Maximum designed power | W | ✅ |
| `communication_last_success` | Last successful communication | timestamp | ✅ |
| `communication_duration` | Communication duration | ms | ✅ |
| `communication_blocks` | Blocks received | blocks | ✅ |
| `communication_failures` | Consecutive communication failures | count | ✅ |
| `label_serial_number` | SN | text | ✅ |
| `inverter_serial_number` | Micro-inverter SN | text | ✅ |
| `logger_firmware_version` | Logger firmware version | text | ✅ |
| `logger_mac_address` | Logger MAC address | text | ✅ |
| `logger_wifi_signal` | Logger Wi-Fi signal | % | ✅ |

### Binary sensors and button

| Platform | Entity key | Home Assistant name | Default |
|---|---|---|:---:|
| Binary sensor | `communication_online` | Micro-inverter online | ✅ |
| Binary sensor | `inverter_alarm` | Inverter alarm | ✅ |
| Button | `refresh_data` | Refresh data | ✅ |

---

# 1511 · TITAN

**Status:** ✅ Validated  
**PV inputs:** up to 6, detected progressively

## 1511-specific diagnostics

| Entity key | Home Assistant name | Default |
|---|---|:---:|
| `register_3017_raw` | Raw register 3017 (inverter temperature) | ✅ |
| `register_3018_raw` | Raw register 3018 (meaning unconfirmed) | ✅ |
| `register_3028_raw` | Raw register 3028 (inverter ambient temperature) | ✅ |
| `inverter_operating_state` | Inverter operating state | ✅ |
| `alarm_global_0_raw` | Raw global alarm 0 | ✅ |
| `alarm_global_1_raw` | Raw global alarm 1 | ✅ |
| `alarm_global_2_raw` | Raw global alarm 2 | ✅ |
| `alarm_global_3_raw` | Raw global alarm 3 | ✅ |
| `alarm_secondary_0_raw` | Raw secondary alarm 0 | ✅ |
| `alarm_secondary_1_raw` | Raw secondary alarm 1 | ✅ |
| `alarm_secondary_2_raw` | Raw secondary alarm 2 | ✅ |
| `alarm_secondary_3_raw` | Raw secondary alarm 3 | ✅ |

### Field-observation notes

- `register_3017_raw` and `register_3028_raw` remain available as original raw decimal diagnostics for protocol verification. In parallel, 1.4.1 exposes `inverter_temperature = raw - 40 °C` from register 3017 and `ambient_temperature = raw - 40 °C` from register 3028.
- `register_3018_raw` remains a plain raw diagnostic because its meaning is still unconfirmed.
- Decimal register `2028` (`0x07EC`) is exposed as `output_coefficient_candidate`, displayed as **Power level (candidate)**. The candidate label is intentional until field validation confirms the mapping.
- On validated MP3000 hardware, bit `0x2000` in `alarm_global_1_raw` is repeatedly observed during dawn, dusk and very low irradiance. TSUN Local preserves the raw `8192` value but does not treat that bit alone as a fault. The operating-state entity reports **Standby — low solar input** instead. The exact vendor bit-name remains unconfirmed.

## 1511 PV entities

Every detected PV input exposes voltage, current, power, daily energy, total energy and one raw alarm entity.

| PV | Voltage | Current | Power | Daily energy | Total energy | Raw alarm |
|:---:|---|---|---|---|---|---|
| 1 | `pv1_voltage` | `pv1_current` | `pv1_power` | `pv1_energy_today` | `pv1_energy_total` | `pv1_alarm_raw` |
| 2 | `pv2_voltage` | `pv2_current` | `pv2_power` | `pv2_energy_today` | `pv2_energy_total` | `pv2_alarm_raw` |
| 3 | `pv3_voltage` | `pv3_current` | `pv3_power` | `pv3_energy_today` | `pv3_energy_total` | `pv3_alarm_raw` |
| 4 | `pv4_voltage` | `pv4_current` | `pv4_power` | `pv4_energy_today` | `pv4_energy_total` | `pv4_alarm_raw` |
| 5 | `pv5_voltage` | `pv5_current` | `pv5_power` | `pv5_energy_today` | `pv5_energy_total` | `pv5_alarm_raw` |
| 6 | `pv6_voltage` | `pv6_current` | `pv6_power` | `pv6_energy_today` | `pv6_energy_total` | `pv6_alarm_raw` |

All rows above are **🔄 dynamic**: only PV inputs detected by TSUN Local are created.

## 1511 advanced diagnostics

All entities below are **🛡️ disabled by default**.

| Entity key | Home Assistant name | Unit |
|---|---|---:|
| `grid_overvoltage_recovery_voltage` | Grid overvoltage recovery voltage | V |
| `grid_undervoltage_recovery_voltage` | Grid undervoltage recovery voltage | V |
| `grid_overfrequency_recovery_frequency` | Grid overfrequency recovery frequency | Hz |
| `grid_underfrequency_recovery_frequency` | Grid underfrequency recovery frequency | Hz |
| `grid_undervoltage_level_1` | Grid undervoltage level 1 | V |
| `grid_undervoltage_level_2` | Grid undervoltage level 2 | V |
| `grid_undervoltage_time_1` | Grid undervoltage time 1 | s |
| `grid_undervoltage_time_2` | Grid undervoltage time 2 | s |
| `grid_overvoltage_level_1` | Grid overvoltage level 1 | V |
| `grid_overvoltage_level_2` | Grid overvoltage level 2 | V |
| `grid_overvoltage_time_1` | Grid overvoltage time 1 | s |
| `grid_overvoltage_time_2` | Grid overvoltage time 2 | s |
| `grid_underfrequency_level_1` | Grid underfrequency level 1 | Hz |
| `grid_underfrequency_level_2` | Grid underfrequency level 2 | Hz |
| `grid_underfrequency_time_1` | Grid underfrequency time 1 | s |
| `grid_underfrequency_time_2` | Grid underfrequency time 2 | s |
| `grid_overfrequency_level_1` | Grid overfrequency level 1 | Hz |
| `grid_overfrequency_level_2` | Grid overfrequency level 2 | Hz |
| `grid_overfrequency_time_1` | Grid overfrequency time 1 | s |
| `grid_overfrequency_time_2` | Grid overfrequency time 2 | s |
| `grid_undervoltage_level_3` | Grid undervoltage level 3 | V |
| `grid_undervoltage_time_3` | Grid undervoltage time 3 | s |
| `inverter_temperature` | Inverter temperature | °C |
| `ambient_temperature` | Inverter ambient temperature | °C |
| `output_coefficient_candidate` | Power level (candidate) | % |

---

# 02B0 · GEN3 PLUS

**Status:** ✅ Validated  
**PV inputs:** up to 4, detected dynamically

## 02B0-specific diagnostics

| Entity key | Home Assistant name | Default |
|---|---|:---:|
| `alarm_code_1_raw` | Raw alarm code 1 | ✅ |
| `alarm_code_2_raw` | Raw alarm code 2 | ✅ |
| `alarm_code_3_raw` | Raw alarm code 3 | ✅ |
| `alarm_code_4_raw` | Raw alarm code 4 | ✅ |

## 02B0 PV entities

| PV | Voltage | Current | Power | Daily energy | Total energy |
|:---:|---|---|---|---|---|
| 1 | `pv1_voltage` | `pv1_current` | `pv1_power` | `pv1_energy_today` | `pv1_energy_total` |
| 2 | `pv2_voltage` | `pv2_current` | `pv2_power` | `pv2_energy_today` | `pv2_energy_total` |
| 3 | `pv3_voltage` | `pv3_current` | `pv3_power` | `pv3_energy_today` | `pv3_energy_total` |
| 4 | `pv4_voltage` | `pv4_current` | `pv4_power` | `pv4_energy_today` | `pv4_energy_total` |

All rows above are **🔄 dynamic**.

## 02B0 advanced diagnostics

All entities below are **🛡️ disabled by default**.

| Entity key | Home Assistant name | Unit |
|---|---|---:|
| `grid_overvoltage_recovery_voltage` | Grid overvoltage recovery voltage | V |
| `grid_undervoltage_recovery_voltage` | Grid undervoltage recovery voltage | V |
| `grid_overfrequency_recovery_frequency` | Grid overfrequency recovery frequency | Hz |
| `grid_underfrequency_recovery_frequency` | Grid underfrequency recovery frequency | Hz |
| `grid_undervoltage_level_1` | Grid undervoltage level 1 | V |
| `grid_undervoltage_level_2` | Grid undervoltage level 2 | V |
| `grid_undervoltage_time_1` | Grid undervoltage time 1 | s |
| `grid_undervoltage_time_2` | Grid undervoltage time 2 | s |
| `grid_overvoltage_level_1` | Grid overvoltage level 1 | V |
| `grid_overvoltage_level_2` | Grid overvoltage level 2 | V |
| `grid_overvoltage_time_1` | Grid overvoltage time 1 | s |
| `grid_overvoltage_time_2` | Grid overvoltage time 2 | s |
| `grid_underfrequency_level_1` | Grid underfrequency level 1 | Hz |
| `grid_underfrequency_level_2` | Grid underfrequency level 2 | Hz |
| `grid_underfrequency_time_1` | Grid underfrequency time 1 | s |
| `grid_underfrequency_time_2` | Grid underfrequency time 2 | s |
| `grid_overfrequency_level_1` | Grid overfrequency level 1 | Hz |
| `grid_overfrequency_level_2` | Grid overfrequency level 2 | Hz |
| `grid_overfrequency_time_1` | Grid overfrequency time 1 | s |
| `grid_overfrequency_time_2` | Grid overfrequency time 2 | s |
| `grid_undervoltage_level_3` | Grid undervoltage level 3 | V |
| `grid_undervoltage_time_3` | Grid undervoltage time 3 | s |
| `output_coefficient` | Power level | % |

---

# 1097 · GEN3

**Status:** 🧪 Experimental  
**PV inputs:** up to 6, detected dynamically

## 1097-specific diagnostics

| Entity key | Home Assistant name | Default |
|---|---|:---:|
| `alarm_code_1_raw` | Raw alarm code 1 | ✅ |
| `alarm_code_2_raw` | Raw alarm code 2 | ✅ |
| `alarm_code_3_raw` | Raw alarm code 3 | ✅ |
| `alarm_code_4_raw` | Raw alarm code 4 | ✅ |

## 1097 PV entities

| PV | Voltage | Current | Power | Daily energy | Total energy |
|:---:|---|---|---|---|---|
| 1 | `pv1_voltage` | `pv1_current` | `pv1_power` | `pv1_energy_today` | `pv1_energy_total` |
| 2 | `pv2_voltage` | `pv2_current` | `pv2_power` | `pv2_energy_today` | `pv2_energy_total` |
| 3 | `pv3_voltage` | `pv3_current` | `pv3_power` | `pv3_energy_today` | `pv3_energy_total` |
| 4 | `pv4_voltage` | `pv4_current` | `pv4_power` | `pv4_energy_today` | `pv4_energy_total` |
| 5 | `pv5_voltage` | `pv5_current` | `pv5_power` | `pv5_energy_today` | `pv5_energy_total` |
| 6 | `pv6_voltage` | `pv6_current` | `pv6_power` | `pv6_energy_today` | `pv6_energy_total` |

All rows above are **🔄 dynamic**.

## 1097 advanced diagnostics

All entities below are **🛡️ disabled by default**.

| Entity key | Home Assistant name | Unit / type |
|---|---|---|
| `protocol_version` | Protocol version | text |
| `inverter_version` | Inverter version | text |
| `insulation_impedance_rx` | Insulation impedance RX | MΩ |
| `insulation_impedance_ry` | Insulation impedance RY | MΩ |
| `inverter_temperature` | Inverter temperature | °C |
| `output_coefficient` | Power level | % |
| `country_profile_raw` | Country/profile code | raw |

---

## Field semantics and display-unit migration in 1.4.1

Grid-protection timing values are native **seconds**. The one-time migration introduced in 1.4.0 still moves beta-era automatic `ms` display choices back to `s` without replacing an explicit user-selected unit.

For 02B0, register `0x202C` is now **Power level** with confirmed `raw × 100 / 1024` scaling (`1024 = 100%`). For 1511, registers 3017 and 3028 are decoded as temperatures using `raw - 40 °C`, while their original raw diagnostics remain available. The 1511 power-level register remains explicitly marked **candidate**.

---

## Enabling advanced entities

Advanced diagnostics are deliberately disabled by default.

In Home Assistant:

**Settings → Devices & services → TSUN Local → Device → Entities → Disabled entities**

Enable only the diagnostics you want to expose.

---

*Entity reference for TSUN Local 1.4.1.*


---

## 1.4.1 field semantics

| Protocol | Entity | Register | Decode | Unit | Confidence |
|---|---|---:|---|:---:|---|
| 02B0 | **Power level** | `0x202C` | `raw × 100 / 1024` | `%` | Confirmed scaling |
| 1511 | **Inverter temperature** | `3017` (`0x0BC9`) | `raw - 40` | `°C` | Mapped temperature |
| 1511 | **Inverter ambient temperature** | `3028` (`0x0BD4`) | `raw - 40` | `°C` | Mapped temperature |
| 1511 | **Power level (candidate)** | `2028` (`0x07EC`) | `raw × 100 / 1024` | `%` | Candidate — field validation required |
| 1511 | Raw register 3018 | `3018` (`0x0BCA`) | raw | — | Meaning unconfirmed |
| 1097 | **Power level** | `0x1423` | `raw × 100 / 1024` | `%` | Experimental 1097 mapping |

For 1511, the raw 3017/3018/3028 diagnostic registers remain available alongside the semantic temperature entities. This makes it possible to verify the decoded values without losing the original protocol data.

The 1097 adapter remains experimental as a whole; its advanced fields should be treated accordingly until validated on additional real hardware.
