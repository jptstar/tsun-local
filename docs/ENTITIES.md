# TSUN Local — Entity reference

[← Back to the main README](../README.md) · [Visual entity reference](https://jptstar.github.io/tsun-local/entities.html) · [Sunology PLAY2](https://jptstar.github.io/tsun-local/sunology-play2.html)

This reference lists the Home Assistant entities exposed by TSUN Local **by local protocol family**.

> [!NOTE]
> The exact number of entities depends on the detected protocol, the number of PV inputs returned by the inverter and the data supported by the active hardware/logger revision. PV entities are created dynamically.

## Compatibility summary

| Protocol | Validated hardware | Status |
|:---:|---|:---:|
| **1511** | TITAN · **TSOL-MP3000** | ✅ Validated |
| **02B0** | GEN3 / GEN3 PLUS · **TSOL-MX500 · Sunology PLAY2** | ✅ Validated |
| **1097** | GEN3 / GEN3 PLUS | 🧪 Experimental |

The Sunology PLAY2 has been validated through the normal automatic TSUN Local Home Assistant setup on real hardware. The tested logger path is Solarman V5 / TCP 8899 with the explicit `0x02B0` sensor-list selector and an embedded Modbus RTU FC03 response.

---

## Common production entities

### AC

| Entity key | Home Assistant name | Unit | Default |
|---|---|---:|:---:|
| `ac_voltage` | AC voltage | V | ✅ |
| `ac_current` | AC current | A | ✅ |
| `ac_frequency` | AC frequency | Hz | ✅ |
| `ac_power` | AC power | W | ✅ |
| `ac_energy_today` | AC energy today | kWh | ✅ |
| `ac_energy_total` | Total AC energy | kWh | ✅ |
| `dc_power_total` | Total DC power | W | ✅ |

### PV inputs

For each detected PV input `N`, TSUN Local can expose:

| Entity key | Home Assistant name | Unit | Default |
|---|---|---:|:---:|
| `pvN_voltage` | PVN voltage | V | ✅ |
| `pvN_current` | PVN current | A | ✅ |
| `pvN_power` | PVN power | W | ✅ |
| `pvN_energy_today` | PVN energy today | kWh | ✅ |
| `pvN_energy_total` | PVN total energy | kWh | ✅ |

PV rows are **dynamic**. Inputs that are not detected are not created merely to fill a fixed model template.

---

## Communication and device entities

| Entity key | Home Assistant name | Unit / type | Default |
|---|---|---|:---:|
| `communication_online` | Micro-inverter online | binary sensor | ✅ |
| `communication_last_success` | Last successful communication | timestamp | ✅ |
| `communication_duration` | Communication duration | ms | ✅ |
| `communication_blocks` | Blocks received | count | ✅ |
| `communication_failures` | Consecutive communication failures | count | ✅ |
| `label_serial_number` | SN | text | ✅ |
| `inverter_serial_number` | Micro-inverter SN | text | ✅ |
| `logger_firmware_version` | Logger firmware version | text | ✅ when available |
| `dsp_firmware_version` | DSP firmware version | text | ✅ when available |
| `qcpu1_firmware_version` | QCPU1 firmware version | text | ✅ when available |
| `qcpu2_firmware_version` | QCPU2 firmware version | text | ✅ when available |
| `logger_mac_address` | Logger MAC address | text | ✅ when available |
| `logger_wifi_signal` | Logger Wi-Fi signal | % | ✅ when available |
| `rated_power` | Rated inverter power | W | ✅ when available |
| `max_designed_power` | Maximum designed power | W | ✅ when available |
| `inverter_status_raw` | Raw inverter status | raw | ✅ |
| `refresh_data` | Refresh data | button | ✅ |

---

## 🚨 Alarm interface

TSUN Local keeps the normal Home Assistant interface compact rather than creating one permanent entity for every alarm bit.

### Stable interface

| Entity key | Home Assistant name | Purpose |
|---|---|---|
| `inverter_alarm` | Inverter alarm | Problem binary sensor |
| `alarm_active_count` | Active alarms | Number of active positions |
| `active_alarm_names` | Active alarm names | Readable active alarm descriptions |

### 1.5.3 beta — clear-text alarms across all three protocols

The current beta unifies the alarm catalogue for **1511, 02B0 and 1097**. Active alarms are displayed as a human-readable localized description with a stable protocol-position code:

```text
Grid undervoltage (02B0-A014)
PV1 input voltage too low (1511-A137)
Unidentified inverter alarm (1097-A041)
```

Known mappings receive clear functional wording. Unknown or reserved positions remain fully visible with neutral wording instead of guessed semantics.

| Protocol | Catalogue positions | Raw words kept as advanced diagnostics |
|---|---:|---:|
| **1511** | **224** | 14 |
| **02B0** | **64** | 4 |
| **1097** | **64** | 4 |

Alarm text is localized in English, French, German, Spanish, Italian, Dutch, Polish and Simplified Chinese.

---

# 1511 · TITAN

**Status:** ✅ validated on **TSOL-MP3000**  
**PV inputs:** up to 6, detected dynamically

The 1511 adapter exposes the richest diagnostic set currently validated in TSUN Local.

### 1511-specific entities and diagnostics

| Entity key | Home Assistant name | Default |
|---|---|:---:|
| `inverter_operating_state` | Inverter operating state | ✅ |
| `inverter_temperature` | Inverter temperature | ✅ / protocol data |
| `ambient_temperature` | Inverter ambient temperature | ✅ / protocol data |
| `register_3018_raw` | Raw register 3018 | ✅ diagnostic |
| `alarm_global_0_raw` … `alarm_global_3_raw` | Raw global alarm words | 🛡️ |
| `alarm_secondary_0_raw` … `alarm_secondary_3_raw` | Raw controller alarm words | 🛡️ |
| `pv1_alarm_raw` … `pv6_alarm_raw` | Raw PV alarm words | 🛡️ dynamic |

### 1511 alarm coverage

The MP3000 catalogue preserves all **224 source positions** from 14 local 16-bit words. Twelve PV mappings have been hardware-observed; remaining positions stay active with neutral wording until independently validated.

### 1511 advanced grid diagnostics

Read-only advanced diagnostics include voltage/frequency protection levels, recovery thresholds, timing values and selected field-validation candidates. They are disabled by default.

Selected field-validation entities include:

- `grid_recovery_rate`
- `grid_overvoltage_10min`
- `grid_overfrequency_reduction_frequency`
- `grid_overfrequency_reduction_coefficient`
- `overtemperature_protection_temperature`
- `grid_start_upper_voltage_limit`
- `grid_start_lower_voltage_limit`
- `grid_start_upper_frequency_limit`
- `grid_start_lower_frequency_limit`
- `grid_qp_voltage_threshold`
- `country_profile_raw`

The live France-configured MP3000 has been observed with `country_profile_raw = 8` at candidate local register `2000 / 0x07D0`; the address remains explicitly documented as a field-validation mapping rather than a vendor-certified semantic source.

See [MP3000 / TITAN field validation](MP3000_FIELD_VALIDATION.md).

---

# 02B0 · GEN3 / GEN3 PLUS

**Status:** ✅ validated on **TSOL-MX500** and **Sunology PLAY2**  
**PV inputs:** up to 4, detected dynamically

The 02B0 family uses the same common AC/PV and communication interface where the data is provided by the device.

### Sunology PLAY2

A real PLAY2 has completed the normal automatic TSUN Local config flow in Home Assistant. The tested logger firmware is `LSW5BLE_17_02B0_1.08-D1`.

For normal PLAY2 installation, use automatic discovery rather than the dedicated research probe.

### 02B0 advanced diagnostics

Depending on the hardware revision, advanced read-only diagnostics can include grid protection values and power-level information.

Raw alarm words remain available as:

- `alarm_code_1_raw`
- `alarm_code_2_raw`
- `alarm_code_3_raw`
- `alarm_code_4_raw`

They are disabled by default; the compact readable alarm interface should be preferred for normal use.

---

# 1097 · GEN3 / GEN3 PLUS

**Status:** 🧪 experimental  
**PV inputs:** up to 6, detected dynamically

The 1097 adapter is informed in part by public protocol research from **Stefan Allius / `s-allius/tsun-gen3-proxy`**. Experimental semantic mappings remain labelled until independently confirmed on broader real hardware.

Advanced diagnostics can include:

- `protocol_version`
- `inverter_version`
- `insulation_impedance_rx`
- `insulation_impedance_ry`
- `inverter_temperature`
- `output_coefficient`
- `country_profile_raw`

The four raw alarm words are kept as disabled-by-default diagnostics, while the 1.5.3 beta uses the same readable compact alarm interface as 1511 and 02B0.

---

## Enabling advanced entities

Advanced diagnostics are deliberately disabled by default.

In Home Assistant:

**Settings → Devices & services → TSUN Local → Device → Entities → Disabled entities**

Enable only the diagnostics you actually need.

---

## Safety

TSUN Local is read-only by design. The integration does not implement inverter configuration writes, grid-protection writes or provisioning changes.
