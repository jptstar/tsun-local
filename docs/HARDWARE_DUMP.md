# TSUN Local Hardware Validation Dump Tool

[← Back to the project README](../README.md)

`tools/tsun_dump.py` creates a standardized hardware-validation capture for TSUN micro-inverters without Home Assistant.

> [!IMPORTANT]
> The tool is **strictly read-only**. It contains no inverter configuration write path. It only uses the local read operations already used by TSUN Local.

The goal is to make real-device validation reproducible across models such as TSOL-MS800, MS1600, MS2000, MX-series devices and TITAN/MP-series hardware.

## ⬇️ Download

**[Download TSUN Local + Hardware Validation Dump Tool (ZIP)](https://github.com/jptstar/tsun-local/archive/refs/heads/main.zip)**

The dump tool reuses the TSUN Local protocol modules, so downloading the repository ZIP is the simplest standalone installation method. No Home Assistant installation is required.

After downloading and extracting the ZIP:

```bash
cd tsun-local-main
python tools/tsun_dump.py
```

For the most complete known-safe hardware-validation capture:

```bash
python tools/tsun_dump.py --full
```

If you know the exact inverter model, include it in the dump metadata and filename:

```bash
python tools/tsun_dump.py --model TSOL-MS800 --full
```

The generated JSON is the file to attach to the relevant TSUN Local testing issue.

## Simplest use

From a clone or extracted ZIP of the TSUN Local repository:

```bash
python tools/tsun_dump.py
```

The tool first sends the same read-only UDP discovery probes used by the TSUN Local diagnostic utilities.

- If one logger and its Monitor SN can be resolved, capture starts automatically.
- If the IP is found but the Monitor SN is not, only the Monitor SN is requested.
- If the Monitor SN is known but an IP was supplied manually, the supplied IP is used.
- If discovery fails completely, the tool asks for the logger IP and then the numeric Monitor SN.
- If several loggers answer, the user chooses which IP to use.

The Monitor SN prompt does not echo the value in the terminal.

Manual parameters remain available when preferred:

```bash
python tools/tsun_dump.py --host 192.168.1.50 --serial 1234567890
```

Using `--serial` can leave the value in shell history, so interactive discovery/prompting is preferred for a dump intended for publication.

## Standard and full modes

The default **standard** mode reads only the established TSUN Local telemetry and diagnostic areas.

```bash
python tools/tsun_dump.py
```

The explicit **full** mode adds only known-safe read ranges useful for protocol research:

```bash
python tools/tsun_dump.py --full
```

`--full` is **not a brute-force scanner**. It does not walk the complete Modbus address space and does not try unknown function codes.

### 02B0

Standard dynamic capture:

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

Supplemental capture includes the known version/profile/diagnostic area. The output deliberately avoids publishing the inverter serial-number words.

### 1511 / TITAN

Only the validated native TITAN read operations are used:

- A1/01 `0x0BB8–0x0BD7`;
- A1/21 `0x07D0–0x082F`;
- A2/02 `0x0CE4–0x0CE7`;
- A3/03 `0x0E10–0x0E2D`;
- A4/04 `0x0ED8–0x0EF5`.

No generic Modbus sweep is attempted on protocol 1511.

## Multiple snapshots

By default the tool takes three dynamic snapshots separated by three seconds:

```text
snapshot 1
snapshot 2  +3 s
snapshot 3  +3 s
```

This lets the JSON classify registers as:

- changing;
- stable;
- always zero;
- always `0xFFFF`;
- incomplete because a read failed.

The number and interval can be changed:

```bash
python tools/tsun_dump.py --snapshots 5 --interval 5
```

Use sensible intervals. The purpose is evidence collection, not high-rate polling.

## Output privacy

The generated JSON does **not** store:

- the logger IP address;
- the Monitor SN used in the AP envelope;
- UDP discovery payloads;
- the AP envelope itself.

The tool keeps raw protocol payloads/register values required for technical validation. Known decoded fields are separated from raw evidence, and unknown registers are not given speculative semantic names.

Typical output name:

```text
tsun_tsol-ms800_02b0_20260820T100412Z.json
```

If no exact model is known:

```text
tsun_gen3-gen3-plus_02b0_20260820T100412Z.json
```

You may explicitly supply the physical model for the metadata/file name:

```bash
python tools/tsun_dump.py --model TSOL-MS800 --full
```

## Before / after configuration validation

Two dumps can be compared without assigning semantic meaning automatically:

```bash
python tools/tsun_dump.py --compare before.json after.json
```

The output lists only raw register changes, for example:

```text
Changed raw registers: 1
  0x2048: 0 -> 1
```

This is intentionally neutral. A changed raw value becomes a semantic mapping only after the external configuration change is known and independently verified.

A comparison JSON can also be saved:

```bash
python tools/tsun_dump.py \
  --compare before.json after.json \
  --output comparison.json
```

## Useful commands

Automatic safe capture:

```bash
python tools/tsun_dump.py
```

Full known-safe research capture:

```bash
python tools/tsun_dump.py --full
```

Force a known protocol if automatic detection needs help:

```bash
python tools/tsun_dump.py --host 192.168.1.50 --protocol 02b0 --full
```

Specify the exact physical model:

```bash
python tools/tsun_dump.py --model TSOL-MS800 --full
```

## Safety design

- read-only UDP discovery;
- no FC06/FC16 Modbus write path;
- Modbus capture plans use FC03 only;
- 02B0/1097 reads are limited to 16 registers per raw request;
- 1511 uses only known native read blocks;
- one failed optional block does not discard successful evidence;
- no address-space brute force;
- no inverter configuration command is implemented.

The safest default remains simply:

```bash
python tools/tsun_dump.py
```
