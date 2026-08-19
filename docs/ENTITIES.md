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
| 🔬 | Field-validation candidate; live read confirmed but semantic validation still pending |

---

## MP3000 entity summary — 1511 with six PV inputs

The maximum 1.5.1-beta.4 MP3000 configuration exposes **108 Home Assistant entities**. The actual number is lower until all six PV inputs have been detected; each additional PV input contributes five production sensors and one disabled raw-alarm diagnostic.

| Group | Maximum | Examples |
|---|---:|---|
| Production and electricity | 37 | AC and PV voltage, current, power, daily energy, total energy |
| Device and logger information | 8 | label SN, inverter SN, logger/DSP/QCPU firmware, MAC address, Wi-Fi signal |
| Temperatures | 2 | inverter and inverter ambient temperature |
| Communication | 5 | online state, last success, duration, blocks, failures |
| Operating state and control | 3 | raw inverter status, operating state, manual refresh |
| Power and capacity diagnostics | 2 | rated power, maximum designed power |
| Grid protection | 22 | voltage/frequency thresholds, recovery values and delays |
| MP3000 field-validation diagnostics | 11 | ten additional A1/21 fields plus raw country/profile candidate |
| Alarm interface | 17 | inverter alarm, active-alarm count, active alarm names, 14 complete raw words |
| Unconfirmed raw diagnostic | 1 | raw register 3018 |
| **Total** | **108** | **59 enabled by default · 49 advanced/disabled by default** |

> [!NOTE]
> The alarm catalogue contains **224 bit positions**, not 224 permanent Home Assistant entities. Active positions are presented through the alarm state, localized alarm-name sensor and count; the 14 complete raw words remain available as disabled diagnostics. The logger, DSP, QCPU1 and QCPU2 firmware versions are exposed. FCPU remains intentionally absent because its local 1511 source register has not yet been identified.

---

## Common entities — 1511 · 02B0 · 1097

These entities are available across the supported protocol families when the corresponding data is provided by the active adapter.

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
| `dsp_firmware_version` | DSP firmware version | text | ✅ |
| `qcpu1_firmware_version` | QCPU1 firmware version | text | ✅ |
| `qcpu2_firmware_version` | QCPU2 firmware version | text | ✅ |
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

**Status:** ✅ Validated on TSOL-MP3000  
**PV inputs:** up to 6, detected progressively

## 1511-specific diagnostics

| Entity key | Home Assistant name | Default |
|---|---|:---:|
| `alarm_active_count` | Active alarms | ✅ |
| `active_alarm_names` | Active alarm names | ✅ |
| `register_3018_raw` | Raw register 3018 (meaning unconfirmed) | ✅ |
| `inverter_operating_state` | Inverter operating state | ✅ |
| `alarm_global_0_raw` … `alarm_global_3_raw` | Four raw global alarm words | 🛡️ |
| `alarm_secondary_0_raw` … `alarm_secondary_3_raw` | Four raw controller alarm words | 🛡️ |
| `pv1_alarm_raw` … `pv6_alarm_raw` | Six raw PV alarm words | 🛡️ 🔄 |

### Field-observation notes

- Register 3017 is exposed as **Inverter temperature** and register 3028 as **Inverter ambient temperature**, both decoded with `raw - 40 °C`.
- Packed 16-bit firmware words are decoded locally with `firmware_version()`: DSP `3008 / 0x0BC0 = 0x1172 → V1.1.72`, QCPU1 `3622 / 0x0E26 = 0x1154 → V1.1.54`, and QCPU2 `3822 / 0x0EEE = 0x1154 → V1.1.54`. FCPU is not guessed.
- `register_3018_raw` remains a plain raw diagnostic because its meaning is still unconfirmed.
- In 1.5.1-beta.4, ten additional A1/21 values are exposed as advanced **field-validation** diagnostics. Their values were read successfully on the live MP3000 and match the TSUN/Talent profile, but they remain semantically pending an independent configuration-change check.
- `country_profile_raw` is now also exposed on 1511 from the leading candidate `2000 / 0x07D0`. The live France-configured MP3000 reads raw `8`. Public 1097 protocol research by **Stefan Allius / s-allius/tsun-gen3-proxy** documents France as country code `8`; the 1511 address itself remains under independent validation.
- The adjacent `0x07D1 = 80` and `0x07D2 = 80` values are documented as the leading pair for the two TSUN/Talent 40.0 s grid connection/reconnection settings with candidate scaling `×0.5 s`. They are **not exposed as separately named Home Assistant entities yet**, because their individual order cannot be proven while both settings have the same value.
- On validated MP3000 hardware, raw value `8192` is repeatedly observed during dawn, dusk and very low irradiance. It remains included in the active-position count and receives a neutral local identifier; the operating-state entity reports **Standby — low solar input**. Its exact meaning still requires control-hardware validation.

## 1511 MP3000 alarm catalogue

The independent local catalogue contains all **224 positions** exposed by the 14 alarm words. Every active position is counted and displayed.

| Catalogue range | Positions | Validation |
|---|---:|---|
| `A001`–`A064` | 64 inverter positions | Control-hardware validation required |
| `A065`–`A128` | 64 controller positions | Control-hardware validation required |
| `A129`–`A224` | 96 PV positions | 12 validated · 84 require control-hardware validation |

The 12 validated mappings cover low PV input voltage and PV DSP faults for PV1 through PV6. The other 212 positions remain fully active and use neutral local wording until their exact meaning is physically validated. The `active_alarm_names` entity publishes the localized alarm text directly; `alarm_active_count` remains the numeric count. Stable Axxx codes are retained only as internal/debug identifiers. The wording is maintained by TSUN Local and is not represented as vendor-certified server terminology.

## 1511 PV entities

Every detected PV input exposes voltage, current, power, daily energy, total energy and one raw alarm entity. Raw alarm entities are disabled by default.

| PV | Voltage | Current | Power | Daily energy | Total energy | Raw alarm |
|:---:|---|---|---|---|---|---|
| 1 | `pv1_voltage` | `pv1_current` | `pv1_power` | `pv1_energy_today` | `pv1_energy_total` | `pv1_alarm_raw` |
| 2 | `pv2_voltage` | `pv2_current` | `pv2_power` | `pv2_energy_today` | `pv2_energy_total` | `pv2_alarm_raw` |
| 3 | `pv3_voltage` | `pv3_current` | `pv3_power` | `pv3_energy_today` | `pv3_energy_total` | `pv3_alarm_raw` |
| 4 | `pv4_voltage` | `pv4_current` | `pv4_power` | `pv4_energy_today` | `pv4_energy_total` | `pv4_alarm_raw` |
| 5 | `pv5_voltage` | `pv5_current` | `pv5_power` | `pv5_energy_today` | `pv5_energy_total` | `pv5_alarm_raw` |
| 6 | `pv6_voltage` | `pv6_current` | `pv6_power` | `pv6_energy_today` | `pv6_energy_total` | `pv6_alarm_raw` |

All rows above are **🔄 dynamic**: only PV inputs detected by TSUN Local are created.

## 1511 core grid-protection diagnostics

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

## 1511 field-validation diagnostics — 1.5.1 beta

All entries are **🛡️ disabled by default** and carry the evidence status **LIVE DEVICE READ CONFIRMED; CONFIGURATION CHANGE VALIDATION PENDING** unless noted otherwise.

| Entity key | Name | Local register | Unit / decode |
|---|---|---:|---|
| `grid_recovery_rate` | Recovery rate | `2003 / 0x07D3` | s · ×0.5 |
| `grid_overvoltage_10min` | Grid Over Voltage 10 Minutes Protection | `2017 / 0x07E1` | V · ×0.1 |
| `grid_overfrequency_reduction_frequency` | Overfrequency reduction value | `2030 / 0x07EE` | Hz · ×0.01 |
| `grid_overfrequency_reduction_coefficient` | Overfrequency reduction coefficient | `2031 / 0x07EF` | %/Hz · ×0.01 (`4000` → `40.00`) |
| `overtemperature_protection_temperature` | Overtemperature protection value | `2032 / 0x07F0` | °C |
| `grid_start_upper_voltage_limit` | Upper startup voltage limit | `2043 / 0x07FB` | V · ×0.1 |
| `grid_start_lower_voltage_limit` | Lower startup voltage limit | `2044 / 0x07FC` | V · ×0.1 |
| `grid_start_upper_frequency_limit` | Upper startup frequency limit | `2045 / 0x07FD` | Hz · ×0.01 |
| `grid_start_lower_frequency_limit` | Lower startup frequency limit | `2046 / 0x07FE` | Hz · ×0.01 |
| `grid_qp_voltage_threshold` | QP voltage threshold | `2048 / 0x0800` | V |
| `country_profile_raw` | Country/profile code | `2000 / 0x07D0` candidate | raw (`8` observed for France) |

The exported TSUN/Talent country `raw_value = 1008` is retained as profile evidence only and is **not** used as the local country enum. The local semantic reference used for research is France=`8` from Stefan Allius's public 1097 country table.

Additional 1511 advanced diagnostics also include:

| Entity key | Home Assistant name | Unit |
|---|---|---:|
| `inverter_temperature` | Inverter temperature | °C |
| `ambient_temperature` | Inverter ambient temperature | °C |

See [MP3000 / TITAN 1511 field-validation diagnostics](MP3000_FIELD_VALIDATION.md) for the evidence details.

---

# 02B0 · GEN3 / GEN3 PLUS

**Status:** ✅ Validated on TSOL-MX500  
**PV inputs:** up to 4, detected dynamically

## 02B0-specific diagnostics

| Entity key | Home Assistant name | Default |
|---|---|:---:|
| `alarm_code_1_raw` | Raw alarm code 1 | 🛡️ |
| `alarm_code_2_raw` | Raw alarm code 2 | 🛡️ |
| `alarm_code_3_raw` | Raw alarm code 3 | 🛡️ |
| `alarm_code_4_raw` | Raw alarm code 4 | 🛡️ |

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

# 1097 · GEN3 / GEN3 PLUS

**Status:** 🧪 Experimental  
**PV inputs:** up to 6, detected dynamically

The experimental 1097 mapping is informed by public protocol research from **Stefan Allius / `s-allius/tsun-gen3-proxy`**. This includes the country/profile mapping and enumeration used as an external semantic reference; TSUN Local does not present those findings as its own discovery.

## 1097-specific diagnostics

| Entity key | Home Assistant name | Default |
|---|---|:---:|
| `alarm_code_1_raw` | Raw alarm code 1 | 🛡️ |
| `alarm_code_2_raw` | Raw alarm code 2 | 🛡️ |
| `alarm_code_3_raw` | Raw alarm code 3 | 🛡️ |
| `alarm_code_4_raw` | Raw alarm code 4 | 🛡️ |

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

## Enabling advanced entities

Advanced diagnostics are deliberately disabled by default.

In Home Assistant:

**Settings → Devices & services → TSUN Local → Device → Entities → Disabled entities**

Enable only the diagnostics you want to expose.
