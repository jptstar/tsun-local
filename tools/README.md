# TSUN Local tools

Diagnostic and validation utilities for TSUN Local.

## Desktop diagnostic — Windows, macOS and Linux

For users who are not comfortable with Python or a command prompt, TSUN Local provides the same desktop diagnostic interface for Windows, macOS and Linux. Every package is built from the shared [`tsun_diagnostic.py`](tsun_diagnostic.py) entry point and uses the same privacy-safe, **strictly read-only** `tsun_dump.py` engine.

All packages are published independently from Home Assistant integration releases under the stable rolling **`diagnostic-latest`** release. The historical Windows URL is deliberately unchanged so links in older posts continue to work.

| Platform | Download | SHA-256 |
|---|---|---|
| Windows x86_64 | [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe) | [checksum](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe.sha256) |
| macOS — Mac M1 / M2 / M3 / M4… (Apple Silicon) | [TSUN-Local-Diagnostic-macOS-arm64.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-arm64.zip) | [checksum](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-arm64.zip.sha256) |
| macOS — Mac Intel (older Macs) | [TSUN-Local-Diagnostic-macOS-x86_64.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-x86_64.zip) | [checksum](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-macOS-x86_64.zip.sha256) |
| Linux x86_64 | [TSUN-Local-Diagnostic-Linux-x86_64](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Linux-x86_64) | [checksum](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Linux-x86_64.sha256) |
| Linux arm64 | [TSUN-Local-Diagnostic-Linux-arm64](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Linux-arm64) | [checksum](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Linux-arm64.sha256) |

> **Which Mac should I download?**  
> • **Apple chip M1, M2, M3, M4 or newer** → choose **Mac M1 / M2 / M3 / M4… (Apple Silicon)**.  
> • **About This Mac says Intel** → choose **Mac Intel**.

Current desktop GUI: **1.5.11** · dump engine: **2.7.4**.

The interface is intentionally harmonized across platforms:

1. **Disable TSUN Local** for the logger being tested.
2. **Run the diagnostic**.
3. **Direct report upload** — recommended; explicit consent is mandatory.
4. **Manual e-mail report** — optional fallback.

The direct-upload dialog keeps the tester name/pseudonym and selected micro-inverter models/quantities in a durable per-user profile, but **never stores the consent checkbox**. Up to 10 searchable model rows are available, including **Sunology PLAY 2**. After a successful upload, the application displays the `TSL-...` receipt and the private-token Worker link that lets the tester see exactly the anonymized report that was sent; it never exposes the private reports repository.

Recommended sequence for a communication problem:

1. Keep the communication problem present and do **not** reload TSUN Local first.
2. Download the Home Assistant diagnostic when possible.
3. Disable the affected TSUN Local config entry.
4. Start the desktop diagnostic and confirm that TSUN Local is disabled.
5. Leave logger IP and Monitor SN empty when automatic discovery works.
6. Run the diagnostic.
7. Use **step 3** to upload the anonymized report after reviewing/accepting the explicit consent text, or use **step 4** e-mail fallback if direct upload is unavailable.
8. Re-enable the TSUN Local config entry.

For an upload-only test away from the installation, the dedicated synthetic mode uses exactly:

```text
Logger IP : 89:89:89:89
Monitor SN: 89898989
```

No logger or micro-inverter is contacted in that mode; the generated report is explicitly marked as synthetic.

### Updates

All packages use the same `diagnostic-latest` manifest and SHA-256 metadata.

- **Windows:** keeps the existing verified in-place self-update flow and the existing download URL.
- **macOS / Linux:** checks the same architecture-specific rolling package and reports when a newer GUI is available. Package replacement is manual for now.
- **Python dumper:** keeps its verified self-update behavior.

Tester profile data is stored outside the executable/application bundle, so replacing a package does not remove the saved tester name or micro-inverter list.

### First launch notes

The macOS packages are ad-hoc signed but **not yet notarized by Apple**. If macOS says **“Apple cannot verify that this app is free of malware”**, click **Done**, then open **Apple menu → System Settings → Privacy & Security**, scroll to **Security**, click **Open Anyway**, authenticate, then confirm **Open**. Apple says this override is available for about one hour after the failed launch attempt. If macOS instead says the app **will damage your Mac** or explicitly reports malware, **do not bypass that warning**. See [Apple’s official instructions](https://support.apple.com/en-gb/102445). 

Linux downloads are portable executables. If the browser removes the executable bit, restore it once:

```bash
chmod +x TSUN-Local-Diagnostic-Linux-x86_64
./TSUN-Local-Diagnostic-Linux-x86_64
```

Use `TSUN-Local-Diagnostic-Linux-arm64` instead on arm64 Linux.

📋 [Cross-platform desktop/direct-upload validation protocol](../docs/DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)

## Hardware validation dump

[`tsun_dump.py`](tsun_dump.py) is the single-file, standalone, privacy-safe and **strictly read-only** hardware dumper for protocols **1511**, **02B0** and **1097**.

### Desktop diagnostic

The desktop packages above are the recommended route for end users. They use the same read-only dump engine and create the same anonymized JSON evidence, with direct report upload added as a separate HTTPS action only after explicit consent.

### Python / command-line version

Direct rolling-release download:

[`https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py`](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py)

Checksum:

[`https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py.sha256`](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py.sha256)

Run with Python 3.10+:

```bash
python3 tsun_dump.py --full
```

The standalone Python file checks the same `diagnostic-latest` manifest on startup, downloads a newer `tsun_dump.py` when available, verifies SHA-256, atomically replaces the current script and restarts. `--no-update` disables the check for one run and `--check-update` only reports availability. If the script location is not writable, the diagnostic continues with the local version and never requests `sudo`.

Dump engine **2.7.4** preserves the strictly read-only logger/protocol research path, including the bounded passive logger-web capture and the getter-only `AT+WSDNS` capability probe. The actual DNS server address is deliberately excluded from the shareable JSON.

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
