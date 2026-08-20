# TSUN Local Hardware Validation Dump Tool

[← Back to the project README](../README.md)

`tsun_dump.py` creates a standardized hardware-validation capture for TSUN micro-inverters without Home Assistant and without installing TSUN Local.

> [!IMPORTANT]
> The tool is **strictly read-only**. It contains no inverter configuration write path. It only implements the local read operations needed for hardware validation.

## ⬇️ Download one file

**[Download `tsun_dump.py`](https://raw.githubusercontent.com/jptstar/tsun-local/main/tools/tsun_dump.py)**

That single Python file is enough. It uses **only the Python standard library**: no Home Assistant, pip package, Node.js or cloned repository is required.

### macOS / Linux

Save the file as `tsun_dump.py`, open Terminal in the same folder, then run:

```bash
python3 tsun_dump.py --full
```

For example, when the file is in Downloads:

```bash
cd ~/Downloads
python3 tsun_dump.py --full
```

### Windows

From PowerShell or Command Prompt in the folder containing the file:

```powershell
py tsun_dump.py --full
```

Python **3.10 or newer** is required.

## Automatic discovery and fallback

The tool first sends read-only UDP discovery probes on the local network.

- IP + Monitor SN found → capture starts automatically.
- IP found but Monitor SN missing → only the Monitor SN is requested.
- IP supplied manually and Monitor SN discovered → the supplied IP is used.
- Discovery fails → the tool asks for the logger IP and then the Monitor SN.
- Several loggers found → the user selects one.

The interactive Monitor SN entry is hidden on screen.

Manual parameters remain available:

```bash
python3 tsun_dump.py --host 192.168.1.50 --serial 1234567890 --full
```

For a dump intended for publication, interactive entry is preferable because `--serial` can remain in shell history.

## Exact model

If the physical inverter model is known, include it in the generated metadata and filename:

```bash
python3 tsun_dump.py --model TSOL-MS800 --full
```

Example output:

```text
tsun_tsol-ms800_02b0_20260820T100412Z.json
```

That JSON is the file to attach to the relevant TSUN Local testing issue.

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

By default three dynamic snapshots are taken three seconds apart. This separates registers that are changing from registers that remain stable, zero or `0xFFFF`.

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
- known inverter serial-number register words;
- UDP discovery payloads;
- the AP envelope itself.

It does include:

- raw decimal and hexadecimal register values;
- successful and failed read blocks;
- multiple timestamped snapshots;
- stable/changing/zero/`FFFF` classification;
- established decoded values separately from raw evidence;
- detected protocol and PV-input count;
- dump-tool version;
- the **SHA-256 of the exact `tsun_dump.py` file** used to create the dump.

Unknown research registers are never assigned speculative semantic names by the dumper.

## Safety design

- one standalone auditable Python file;
- Python standard library only;
- read-only UDP discovery;
- Modbus capture implements FC03 reads only;
- **no FC06/FC16 write implementation**;
- 02B0/1097 requests are limited to 16 registers each;
- 1511 uses only known native read commands;
- failed optional blocks do not discard successful evidence;
- no address-space brute force;
- no inverter configuration command.

The normal developer/tester command is simply:

```bash
python3 tsun_dump.py --full
```
