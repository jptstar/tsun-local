# MP3000 / TITAN 1511 — research checkpoint 2026-08-19

This page preserves a dated, reproducible checkpoint of the MP3000 / TITAN 1511 investigation without publishing the complete research dump at this stage.

## Acquisition

- Device family: TSUN MP3000 / TITAN 1511
- Capture timestamp: `2026-08-19T17:37:34.800815Z`
- Acquisition script: `tsun_mp3000_full_readonly_dump_v1.3.3_wifi.py`
- Script version: `1.3.3`
- Mode: `focused`
- Acquisition: **read-only**
- Protocol: `1511 native TITAN over TSUN AP envelope`
- Device/profile country used for this investigation: **France**

## Native blocks successfully read

| Native selector | Register range | Requested | Successful |
|---|---:|---:|---:|
| `A1/21` | `2000–2095` | 96 | 96 |
| `A1/01` | `3000–3031` | 32 | 32 |
| `A2/02` | `3300–3303` | 4 | 4 |
| `A3/03` | `3600–3629` | 30 | 30 |
| `A4/04` | `3800–3829` | 30 | 30 |

This checkpoint therefore records successful live reads of the `A2/02`, `A3/03`, and `A4/04` blocks in addition to the extended `A1/21` configuration/capability area and the main `A1/01` block.

## Country/profile candidate

On the France-configured MP3000 used for this capture:

```text
A1/21 register 2000 (0x07D0) = 8 (0x0008)
```

This is recorded as a **candidate observation**, not as a completed semantic proof. Independent confirmation from a device using a different known country/profile, or another authoritative 1511 mapping, is still required before treating the address as fully demonstrated.

## Preserved evidence fingerprint

A sanitized copy of the complete read-only dump is retained outside this repository under the canonical evidence name:

`tsun_mp3000_fr_1511_readonly_20260819T173734Z.json`

SHA-256:

```text
a66818383d49d942a1d29875ee78bf3554c010744ba53e036de6656f3f639761
```

The same fingerprint is stored in [`evidence/tsun_mp3000_fr_1511_readonly_20260819T173734Z.sha256`](evidence/tsun_mp3000_fr_1511_readonly_20260819T173734Z.sha256).

Publishing the fingerprint now allows any later publication of the complete sanitized JSON to be checked byte-for-byte against this checkpoint.

## Sanitization

Only installation-specific identifiers were replaced in the retained sanitized copy:

- inverter serial number → `<INVERTER_SN>`;
- logger MAC address → `<LOGGER_MAC>`;
- Wi-Fi SSID → `<WIFI_SSID>`.

The host address and logger serial number were already suppressed by the acquisition script. Register addresses, raw values, protocol data, captured web content apart from those identifiers, and analysis fields were not otherwise altered.

## Evidence status

This checkpoint distinguishes three levels deliberately:

1. **Observed:** data present in captures or device/profile material.
2. **Live-read validated:** the register/block was successfully read on the physical MP3000.
3. **Semantically confirmed:** the meaning has been independently distinguished, for example by a controlled setting change, a second differently configured device, or an authoritative mapping.

The existence and readability of the native blocks listed above are live-device observations. Individual field semantics remain subject to the validation status documented in [`MP3000_FIELD_VALIDATION.md`](MP3000_FIELD_VALIDATION.md).
