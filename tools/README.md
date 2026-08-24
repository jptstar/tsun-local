# TSUN Local tools

Diagnostic and validation utilities for TSUN Local.

## Hardware validation dump

[`tsun_dump.py`](tsun_dump.py) is a **single-file, standalone, privacy-safe, strictly read-only** hardware dumper for protocol **1511**, **02B0** and **1097**.

It uses only the Python standard library and does not require Home Assistant or the rest of the TSUN Local repository.

Direct download:

[`https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)

Run it with Python 3.10+:

```bash
python3 tsun_dump.py --full
```

The tool tries local discovery first. IP address and Monitor SN are requested only when automatic discovery cannot resolve them, and neither is stored in the output JSON.

For Windows terminals where interactive input is inconvenient, the Monitor SN can be supplied directly:

```powershell
py tsun_dump.py --host 192.168.1.50 --monitor-sn 1234567890 --full
```

`--monitor-sn` and the legacy `--serial` option are equivalent.

For the capture ranges, safety model, snapshots and before/after comparison, see [Hardware Validation Dump Tool](../docs/HARDWARE_DUMP.md).

## Sunology PLAY2 super-probe

[`tsun_play2_probe.py`](tsun_play2_probe.py) is a standalone, privacy-safe, **strictly read-only** all-in-one diagnostic for PLAY2 / MX variants that do not answer normal TSUN Local protocol detection.

Version **1.2.1** combines the main evidence-driven hypotheses in one run:

- Sunology/iGEN discovery across UDP **48899** and **49999** in both directions, using `smartlinkfind` and the known legacy discovery messages;
- detailed `smart_config` / `##` parsing and correlation of discovered hosts with the supplied Monitor SN;
- DNS-SD/mDNS discovery of `_solarhome._tcp.local` used by Sunology CONNECT;
- passive WebSocket handshake/listen on the mDNS-resolved `ws://<host>:<port>/ws`, including detection of `solarEvent`, `pvP`, battery/grid events and product information;
- HTTP/HTTPS local identity checks on supplied and discovered candidate hosts;
- the same bounded, read-only TCP diagnostic matrix on **8899**, **48899** and **49999**, including AP/Solarman sequence variants, sensor-lists **1511**, **02B0**, **1097**, **3026**, direct Modbus-RTU-over-TCP and Modbus-TCP read hypotheses.

UDP **48899/49999** only receive known discovery strings; binary AP/Modbus probes are never sent to the UDP configuration services. The additional protocol matrix is performed only over TCP when the corresponding TCP port accepts a connection.

The `ws://127.0.0.1:20199` address found in Sunology STREAM 3.2.2 is a **development/local mock only**. The production application resolves the CONNECT endpoint through mDNS, so the probe does not scan port 20199 on the PLAY2.

Run it with Python 3.10+ on Windows:

```powershell
py tsun_play2_probe.py --host 192.168.1.50 --monitor-sn 1234567890
```

One run produces two files:

- `tsun_play2_superprobe_....json` — rich machine-readable diagnostic;
- `tsun_play2_superprobe_....log` — detailed human-readable execution log.

The report aliases local IP addresses and redacts Monitor SN and MAC addresses while retaining packet lengths, hashes, redacted hex/ASCII structure and protocol behaviour useful for reverse engineering.

The probe performs **no cloud request, no BLE/Wi-Fi provisioning, no configuration write and no Modbus write**.

On Windows, Python may need permission through Windows Defender Firewall on the **Private** network so local UDP/mDNS replies can be received. No router port forwarding or Internet-facing port opening is required.

## Existing focused diagnostics

- `diagnose_device.py` — one anonymized TSUN Local protocol poll;
- `diagnose_02b0.py` — focused 02B0 diagnostics;
- `diagnose_logger_web.py` — logger web-interface diagnostics;
- `diagnose_udp_discovery.py` — privacy-safe UDP discovery test;
- `replay_diagnostic.py` — replay diagnostic captures.
