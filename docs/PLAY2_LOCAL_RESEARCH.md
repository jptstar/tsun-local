# Sunology PLAY2 — local protocol research

This document tracks the current read-only local-protocol investigation for Sunology PLAY2 / compatible OEM logger variants.

## Current status

The local transport is no longer considered completely unknown.

- iGEN / High-Flying style UDP discovery is confirmed on ports **49999/48899**.
- The actual responding local logger may be discovered at an address different from the initially supplied host.
- TCP **8899** is confirmed to return valid **Solarman V5** envelopes.
- Local V5 requests use control code **`0x4510`** and observed responses use **`0x1510`**.
- Observed short embedded payloads such as `05 00` and `06 00` are preserved as **unknown logger response markers**. They are not assigned an error meaning without repeatable evidence.
- The remaining V5 research target is the protocol carried inside the response payload.

## Logger identity: PLAY2 MAC vs logger/module MAC candidate

A bare 12-hex token returned by local discovery is no longer treated as an arbitrary identifier, but it is also **not automatically equated with the MAC address visible to the PLAY2 user**.

The historical `WIFIKIT-214028-READ` protocol returns three fields in the form:

```text
<IP>,<base MAC>,<logger serial>
```

The PLAY2 discovery response follows that same structure. In addition, the observed 12-hex token uses OUI `D4:27:87`, associated with High-Flying hardware. The probe therefore records it as a **logger/module MAC candidate** and keeps only its suffix plus an optional vendor hint.

The diagnostic output distinguishes:

- an explicit/separated MAC address, e.g. `AA:BB:CC:DD:EE:FF`;
- a compact 12-hex **logger/module MAC candidate**;
- the PLAY2-visible MAC, which remains a separate identity unless independently correlated.

Full local IP addresses, Monitor SNs, MAC addresses and compact MAC candidates are redacted from evidence fields.

## Diagnostic tool

Use the dedicated PLAY2 read-only probe:

**[`tools/tsun_play2_probe.py`](../tools/tsun_play2_probe.py)**

Current diagnostic version: **v1.3.2**.

Windows example:

```powershell
py tsun_play2_probe.py --host PLAY2_IP --monitor-sn MONITOR_SN
```

The tool automatically performs:

1. UDP logger discovery and identity correlation;
2. mDNS / CONNECT-Hub checks;
3. read-only HTTP identity requests;
4. TCP 8899 Solarman V5 read probes;
5. a short read-only same-connection V5 sequence for session-sensitive loggers;
6. embedded-payload classification as Modbus RTU, TSUN-native candidate, unknown protocol, or short marker;
7. **one historical Solarman/iGEN V4 read cross-check** on a strong logger candidate.

It generates one JSON report and one LOG file. Both are useful for field validation.

## Historical V4 cross-check

Version **v1.3.2** adds a deliberately narrow legacy test based on the documented High-Flying / Solarman V4 local protocol.

The request is the historical **command `0x0001` (read inverter data)**:

```text
68 | 02 | 41 B1 | logger SN | logger SN | 01 00 | checksum | 16
```

The probe sends this command **once**, only on TCP 8899 for a logger candidate already strengthened by local discovery, and only when a Monitor/logger SN was supplied.

If a valid historical V4 telemetry frame is returned, the probe can conservatively decode the documented `81 02 01` layout into candidate values such as temperature, PV voltage/current, AC voltage/current/frequency/power, daily energy and total energy. Those values are labelled as telemetry candidates only when the response matches that historical layout.

This V4 test does **not** imply that PLAY2 uses V4 in normal operation. It is a compatibility cross-check intended to determine whether the High-Flying logger still exposes its older local read path in parallel with Solarman V5.

## Safety

The probe is intentionally read-only:

- Modbus functions sent: **FC03 / FC04 only**;
- one historical V4 **read** command: `0x0001`;
- no Modbus write functions;
- no inverter configuration commands;
- no BLE/Wi-Fi provisioning;
- no cloud login or cloud telemetry request;
- no WebSocket application messages.

## Success criteria

Either of these would be a decisive result:

- a valid `0x1510` response containing an embedded payload longer than two bytes that can be identified reproducibly as Modbus RTU, TSUN native, or another repeatable protocol;
- a valid historical V4 inverter telemetry frame returned by command `0x0001`.

Either result would expose the inverter-side local data path and allow the next step: mapping actual PLAY2 solar telemetry independently from the already-confirmed discovery and transport layers.
