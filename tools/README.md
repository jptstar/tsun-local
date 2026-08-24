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

## Existing focused diagnostics

- `diagnose_device.py` — one anonymized TSUN Local protocol poll;
- `diagnose_02b0.py` — focused 02B0 diagnostics;
- `diagnose_logger_web.py` — logger web-interface diagnostics;
- `diagnose_udp_discovery.py` — privacy-safe UDP discovery test;
- `replay_diagnostic.py` — replay diagnostic captures.
