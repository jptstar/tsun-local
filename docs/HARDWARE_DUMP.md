# TSUN Local Hardware Validation Dump Tool

[← Back to the project README](../README.md)

`tsun_dump.py` creates standardized hardware-validation captures for TSUN micro-inverters without Home Assistant and without installing TSUN Local.

> [!IMPORTANT]
> The tool is **strictly read-only**. It contains no inverter configuration write path. It only implements the local read operations needed for hardware validation.

## ⬇️ Choose the easiest diagnostic

### Windows — portable executable (recommended for end users)

**[Download `TSUN-Local-Diagnostic.exe`](https://github.com/jptstar/tsun-local/releases/latest/download/TSUN-Local-Diagnostic.exe)**  
**[SHA-256 checksum](https://github.com/jptstar/tsun-local/releases/latest/download/TSUN-Local-Diagnostic.exe.sha256)**

No installation and no Python environment are required. The executable is built from the same **strictly read-only** `tsun_dump.py` engine and creates the same privacy-safe JSON reports.

When diagnosing a communication failure or unavailable entities:

1. reproduce the problem and **do not reload TSUN Local first**;
2. download the Home Assistant diagnostic when possible;
3. **disable the affected TSUN Local config entry** so it does not compete for the logger connection;
4. run `TSUN-Local-Diagnostic.exe` and start the full diagnostic;
5. re-enable TSUN Local when the capture is finished;
6. send the generated JSON file(s) together with the Home Assistant diagnostic.

The Windows executable is currently unsigned, so Windows SmartScreen may show an **Unknown publisher** warning. The published SHA-256 file can be used to verify the download.

### Python script — macOS, Linux and advanced users

**[Download `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

The single Python file uses **only the Python standard library**: no Home Assistant, pip package, Node.js or cloned repository is required. Python **3.10 or newer** is required.

macOS / Linux:

```bash
python3 tsun_dump.py --full
```

Windows terminal alternative:

```powershell
py tsun_dump.py --full
```

If the Monitor SN is already known, it can be passed directly:

```powershell
py tsun_dump.py --host 192.168.1.50 --monitor-sn 1234567890 --full
```

`--monitor-sn` is an alias for the existing `--serial` option.

## Automatic discovery: all devices by default

The tool first sends repeated read-only UDP discovery probes. It then performs a **bounded TCP scan on port 8899** for each discovered `/24` (and for each network supplied with `--network`) and directly UDP-probes TCP-only candidates. **When `--host` is not supplied, every resulting candidate is validated and a separate JSON dump is generated for each supported TSUN logger.**

Example with three discovered loggers:

```text
Searching the local network for all TSUN loggers (read-only UDP)...
3 candidate logger(s) found. Every discovered logger will be captured.

=== Device 1/3 ===
...
=== Device 2/3 ===
...
=== Device 3/3 ===
...
```

Typical multi-device output files are kept distinct automatically:

```text
tsun_device-01_unknown_02b0_20260820T100412Z.json
tsun_device-02_unknown_1511_20260820T100438Z.json
tsun_device-03_unknown_1097_20260820T100501Z.json
```

Discovery behavior:

- all discovered loggers with a resolved Monitor SN → all are captured automatically;
- one discovered logger with a missing Monitor SN → only that SN is requested;
- several discovered loggers and one has a missing/ambiguous Monitor SN → the SN is requested for that logger; pressing Enter skips only that logger and continues with the others;
- one device fails during protocol detection or capture → the script continues with the remaining devices;
- no logger is discovered → the tool falls back to asking for one logger IP and Monitor SN;
- `--host` supplied → intentional single-device mode.

Interactive Monitor SN entry uses normal terminal input for compatibility with Windows, PowerShell, Command Prompt and other consoles. The Monitor SN is still excluded from generated JSON files.

To target only one known logger:

```bash
python3 tsun_dump.py --host 192.168.1.50 --full
```

Or provide both values manually:

```bash
python3 tsun_dump.py --host 192.168.1.50 --monitor-sn 1234567890 --full
```

The legacy spelling remains supported:

```bash
python3 tsun_dump.py --host 192.168.1.50 --serial 1234567890 --full
```

For a dump intended for publication, remember that a Monitor SN supplied on the command line may remain in shell history even though it is not written to the dump JSON.

> [!NOTE]
> UDP broadcast discovery normally stays inside the local broadcast domain. For a routed VLAN/subnet, use a bounded network scan such as:
>
> ```bash
> python3 tsun_dump.py --network 10.89.10.0/24 --full
> ```
>
> `--network` accepts only `/24` or smaller IPv4 networks and may be repeated. If one logger is found by UDP, its `/24` is scanned automatically, which can reveal neighboring TSUN loggers that do not answer broadcast discovery.

## Exact model

If the physical inverter model is known, include it in the generated metadata and filename:

```bash
python3 tsun_dump.py --model TSOL-MS800 --full
```

When several devices are discovered, the same `--model` value applies to every generated dump, so omit it if the network contains different models unless you are certain they are identical.

Single-device example output:

```text
tsun_tsol-ms800_02b0_20260820T100412Z.json
```

The generated JSON files are what should be attached to the relevant TSUN Local testing issue.

## Standard and full modes

The default mode reads established TSUN Local telemetry/diagnostic areas:

```bash
python3 tsun_dump.py
```

The explicit `--full` mode adds only known-safe research ranges:

```bash
python3 tsun_dump.py --full
```

`--full` is **not a brute-force scanner**. It does not walk the complete register address space and does not try unknown function codes.

### 02B0

Dynamic capture:

- FC03 `0x3000–0x302F`, split into conservative 16-register requests.

Standard supplemental diagnostics:

- `0x2007`;
- `0x2014–0x202C`.

Full supplemental capture:

- FC03 `0x2000–0x204F`, including the public research area around `0x2047–0x204A`.

### 1097

Dynamic capture:

- FC03 `0x1100–0x110F`;
- FC03 `0x1200–0x121F`;
- FC03 `0x1300–0x132F`.

Supplemental capture includes `0x1008–0x100F` and the known profile/diagnostic area. The inverter serial-number words `0x1000–0x1007` are deliberately excluded from published dumps.

### 1511 / TITAN

Only validated native TITAN read operations are used:

- A1/01 `0x0BB8–0x0BD7`;
- A1/21 `0x07D0–0x082F`;
- A2/02 `0x0CE4–0x0CE7`;
- A3/03 `0x0E10–0x0E2D`;
- A4/04 `0x0ED8–0x0EF5`.

No generic Modbus sweep is attempted on 1511.

## Multiple snapshots

By default three dynamic snapshots are taken three seconds apart for **each captured device**. This separates registers that are changing from registers that remain stable, zero or `0xFFFF`.

```bash
python3 tsun_dump.py --snapshots 5 --interval 5
```

The purpose is evidence collection, not high-rate polling.

## Before / after validation

Two dumps can be compared without automatically assigning semantic meaning:

```bash
python3 tsun_dump.py --compare before.json after.json
```

Example:

```text
Changed raw registers: 1
  0x2048: 0 -> 1
```

A comparison JSON can also be saved:

```bash
python3 tsun_dump.py \
  --compare before.json after.json \
  --output comparison.json
```

This is useful for controlled setting-change validation while keeping the result neutral until the changed register has been independently identified.

## Output privacy

The generated JSON does **not** store:

- logger IP address;
- Monitor SN used by the AP envelope;
- full inverter serial number (only its first 3 characters may be retained as a family/OEM prefix);
- known inverter serial-number register words;
- full logger MAC address (only the OUI may be retained);
- Wi-Fi SSID, Wi-Fi password/PSK, tokens, secrets, email addresses or other recognized credentials from logger web pages;
- raw, non-anonymized logger HTML;
- UDP discovery payloads;
- the AP envelope itself.

It does include:

- anonymized snapshots of the known local logger web pages (`/index_cn.html`, `/index.html`, `/status.html`, `/` and `/hide_set_edit.html`) so future firmware layouts can be re-analysed without requesting a new dump;
- logger firmware, Wi-Fi signal, raw inverter profile (`inv_tp`) when available, MAC OUI only (first three octets), and only the first **3 characters** of the inverter serial number (for example `Y47`);
- raw decimal and hexadecimal register values;
- successful and failed read blocks;
- multiple timestamped snapshots;
- stable/changing/zero/`FFFF` classification;
- established decoded values separately from raw evidence;
- detected protocol and PV-input count;
- dump-tool version;
- the **SHA-256 of the exact `tsun_dump.py` file** used to create the dump;
- a non-sensitive discovery index so multi-device files can be correlated without storing IP or Monitor SN.

Unknown research registers are never assigned speculative semantic names by the dumper.

## Safety design

- one standalone auditable Python file;
- Python standard library only;
- read-only UDP discovery;
- repeated UDP discovery plus bounded `/24` TCP fallback on port 8899;
- direct UDP retry for TCP-only candidates;
- protocol detection retried before a candidate is rejected;
- all discovered loggers processed sequentially, avoiding simultaneous high-rate polling;
- HTTP `admin:admin` is only sent to an explicitly targeted host or after an unauthenticated page has already been identified as TSUN;
- Modbus capture implements FC03 reads only;
- **no FC06/FC16 write implementation**;
- 02B0/1097 requests are limited to 16 registers each;
- 1511 uses only known native read commands;
- failure of one logger does not stop dumps for the others;
- failed optional blocks do not discard successful evidence;
- invalid/non-finite timeout values are rejected before network access;
- Monitor SN values are range-checked before AP framing;
- no address-space brute force;
- no inverter configuration command.

The normal developer/tester command is simply:

```bash
python3 tsun_dump.py --full
```
