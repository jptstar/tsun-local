# Sunology PLAY2 — local protocol research

This document tracks the current read-only local-protocol investigation for Sunology PLAY2 / compatible OEM logger variants.

## Current status

The local transport is no longer considered completely unknown.

- iGEN-style UDP discovery is confirmed on ports **49999/48899**.
- The actual responding local logger may be discovered at an address different from the initially supplied host.
- TCP **8899** is confirmed to return valid **Solarman V5** envelopes.
- Local requests use control code **`0x4510`** and observed responses use **`0x1510`**.
- The remaining research target is the protocol carried inside the V5 response payload.

Observed short embedded payloads such as `05 00` and `06 00` are kept as **unknown response markers**. They are not labelled as Modbus data or error codes until their meaning is demonstrated by repeatable tests.

## Device identity: MAC vs module identifier

A bare 12-hex token returned by local discovery must **not** automatically be treated as the PLAY2 MAC address.

The diagnostic probe therefore distinguishes:

- an explicit/separated MAC address, e.g. `AA:BB:CC:DD:EE:FF`;
- an opaque 12-hex **module identifier**, whose semantics remain unknown.

Only short suffixes are retained in the public diagnostic output. Full local IP addresses, Monitor SNs, MAC addresses and module identifiers are redacted from evidence fields.

## Diagnostic tool

Use the dedicated PLAY2 read-only probe:

**[`tools/tsun_play2_probe.py`](../tools/tsun_play2_probe.py)**

Current diagnostic version: **v1.3.1**.

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
6. embedded-payload classification as Modbus RTU, TSUN-native candidate, unknown protocol, or short marker.

It generates one JSON report and one LOG file. Both are useful for field validation.

## Safety

The probe is intentionally read-only:

- Modbus functions sent: **FC03 / FC04 only**;
- no Modbus write functions;
- no inverter configuration commands;
- no BLE/Wi-Fi provisioning;
- no cloud login or cloud telemetry request;
- no WebSocket application messages.

## Success criterion

The next decisive result is a valid `0x1510` response containing an embedded payload longer than two bytes that can be identified reproducibly as:

- Modbus RTU,
- TSUN native protocol,
- or another repeatable local protocol.

Once that inner payload is identified, PLAY2 telemetry mapping can be investigated independently from the already-confirmed Solarman V5 transport.
