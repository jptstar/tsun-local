# TSUN Local tools

Diagnostic and validation utilities for TSUN Local.

## Windows portable diagnostic

For users who are not comfortable with Python or a command prompt, TSUN Local also provides a portable Windows executable built from the same read-only dump engine. It is published independently from integration releases under `diagnostic-latest`; the current GUI is 1.3.0 and uses the 2.5.0 dump engine.

**⬇️ [Download `TSUN-Local-Diagnostic.exe`](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)**

No installation and no Python environment are required. The executable provides a compact French/English **scroll-free main screen** with the three essential steps visible at once. Advanced settings and technical logs open separately, while the same privacy-safe **strictly read-only** `tsun_dump.py` engine writes the anonymized JSON report into the selected folder.

Recommended sequence:

1. Keep the communication problem present and do **not** reload TSUN Local yet.
2. Disable the affected TSUN Local config entry in Home Assistant.
3. Start `TSUN-Local-Diagnostic.exe` and confirm that the entry is disabled.
4. Leave the logger IP and Monitor SN empty when automatic discovery works; the application asks for missing information only when required.
5. Click **Run full diagnostic / Lancer le diagnostic complet**.
6. Send the generated JSON file to `dev@jptstar.com`, together with the Home Assistant diagnostic when available.
7. Re-enable the TSUN Local config entry.

The Monitor SN, logger IP, SSID, passwords, tokens, e-mail addresses and full MAC addresses are not stored in the generated report. The workflow also publishes a `.sha256` checksum next to the executable.

The executable is currently unsigned, so Windows SmartScreen may display an unknown-publisher warning. The source of the GUI and the complete build workflow are public in this repository.

## Hardware validation dump

[`tsun_dump.py`](tsun_dump.py) is the single-file, standalone, privacy-safe and **strictly read-only** hardware dumper for protocols **1511**, **02B0** and **1097**.

### Windows portable diagnostic

For users who are not comfortable with Python or a command prompt:

**⬇️ [Download `TSUN-Local-Diagnostic.exe`](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)**
**[SHA-256 checksum](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe.sha256)**

No installation or Python environment is required. The French/English GUI uses the same read-only dump engine and writes anonymized JSON reports into the folder selected by the user.

If the capture is intended to diagnose a communication problem, take the Home Assistant diagnostic first when possible, then **disable the affected TSUN Local config entry before running the executable**. Re-enable it after the capture.

### Python / command-line version

Direct download:

[`https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)

Run with Python 3.10+:

```bash
python3 tsun_dump.py --full
```

The tool tries local discovery first. IP address and Monitor SN are requested only when automatic discovery cannot resolve them, and neither is stored in the output JSON. `--monitor-sn` and the legacy `--serial` option are equivalent.

For capture ranges, safety, privacy, snapshots and before/after comparison, see [Hardware Validation Dump Tool](../docs/HARDWARE_DUMP.md).

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
