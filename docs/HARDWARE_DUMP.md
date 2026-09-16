# TSUN Local Hardware Validation Dump Tool

[← Back to the project README](../README.md)

`tsun_dump.py` creates standardized hardware-validation captures for TSUN micro-inverters without Home Assistant and without installing TSUN Local.

> [!IMPORTANT]
> The diagnostic path is **strictly read-only**. It contains no inverter configuration write path.

## Recommended diagnostic

Use one of the two canonical packages from the rolling `diagnostic-latest` release:

| Package | Requirement | Download |
|---|---|---|
| Windows diagnostic | Windows x86_64 · no Python required | [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe) · [SHA-256](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe.sha256) |
| Full Python diagnostic | Python 3.10+ | [TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip) · [SHA-256](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip.sha256) |

Before capture, **disable the affected TSUN Local config entry** so two clients do not compete for the same logger connection. Re-enable it when the test is complete.

The uploader requires explicit consent. The tester name/pseudonym and selected inverter models can be stored locally; consent is never persisted. A successful upload returns a `TSL-...` receipt and a private-token view link for the submitted anonymized report.

📋 [Direct-upload validation protocol](DIRECT_DIAGNOSTIC_UPLOAD_TEST.md)

## Advanced single-file fallback

The historical standalone file remains available for advanced troubleshooting:

**[Download `tsun_dump.py`](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py)** · [SHA-256](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/tsun_dump.py.sha256)

```bash
python3 tsun_dump.py --full
```

On Windows:

```powershell
py tsun_dump.py --full
```

## Discovery and targeting

The tool first performs read-only local discovery. When a logger cannot be resolved automatically, IP address and Monitor SN can be supplied manually. They are not written to the shareable JSON.

Known logger example:

```bash
python3 tsun_dump.py --host 192.168.1.50 --monitor-sn 1234567890 --full
```

For a routed network, a bounded `/24` scan can be requested:

```bash
python3 tsun_dump.py --network 10.89.10.0/24 --full
```

## Capture ranges

### 02B0

- dynamic FC03 reads around `0x3000–0x302F`;
- supplemental diagnostics in `0x2000–0x205F` in full mode;
- requests are split into conservative blocks of at most 16 registers.

### 1097

- dynamic FC03 reads at `0x1100–0x110F`, `0x1200–0x122F` and `0x1300–0x133F`;
- supplemental read-only profile/diagnostic data in full mode;
- inverter serial-number words are deliberately excluded from published dumps.

### 1511 / TITAN

Only validated native TITAN read operations are used:

- A1/01 `0x0BB8–0x0BD7`;
- A1/21 `0x07D0–0x082F`;
- A2/02 `0x0CE4–0x0CE7`;
- A3/03 `0x0E10–0x0E2D`;
- A4/04 `0x0ED8–0x0EF5`.

No generic Modbus sweep is attempted on 1511.

## Multiple snapshots and comparison

Three dynamic snapshots are taken by default. This separates changing values from stable, zero or `0xFFFF` registers.

```bash
python3 tsun_dump.py --snapshots 5 --interval 5
```

Neutral before/after comparison:

```bash
python3 tsun_dump.py --compare before.json after.json
```

## Privacy

The shareable JSON excludes full logger IP addresses, Monitor SN, full inverter serial numbers, complete MAC addresses, Wi-Fi credentials, tokens, secrets and raw non-anonymized logger HTML.

It may include anonymized logger evidence, firmware, Wi-Fi signal metadata, MAC OUI, a short inverter-family prefix, raw register values, read success/failure information, snapshot classification, detected protocol, PV-input count and tool version.

## Safety design

- local read operations only;
- Modbus FC03 reads only;
- no FC06/FC16 write implementation;
- bounded request sizes and network scans;
- no address-space brute force;
- no inverter configuration, reboot, reset or firmware-update command;
- one failed logger does not stop captures for other discovered devices.

Unknown research values remain raw until independently validated.
