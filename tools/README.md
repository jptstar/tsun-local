# TSUN Local tools

Diagnostic and validation utilities for TSUN Local.

## Official diagnostic packages

The public diagnostic release intentionally exposes only two primary packages. Both use the same privacy-safe, **strictly read-only** diagnostic engine.

| Package | Requirement | Download |
|---|---|---|
| Windows diagnostic | Windows x86_64 · no Python required | [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe) · [SHA-256](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe.sha256) |
| Full Python diagnostic | Python 3.10+ | [TSUN-Local-Diagnostic-Python.zip](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip) · [SHA-256](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic-Python.zip.sha256) |

After extracting the Python package:

```bash
python3 tsun_diagnostic_cli.py --full
```

On Windows, `py tsun_diagnostic_cli.py --full` is also supported.

The normal workflow is:

1. disable the affected TSUN Local config entry;
2. run the diagnostic;
3. review the anonymized report;
4. upload only after explicit consent;
5. re-enable TSUN Local when finished.

The historical single-file [`tsun_dump.py`](tsun_dump.py) remains available as an advanced compatibility fallback. It is not the primary public package.

## Hardware validation

[`tsun_dump.py`](tsun_dump.py) performs strictly read-only validation for protocols **1511**, **02B0** and **1097**. It supports automatic discovery, bounded read-only capture, multiple snapshots, neutral before/after comparison and anonymized JSON output.

See [Hardware Validation Dump Tool](../docs/HARDWARE_DUMP.md).

## Sunology PLAY2 research

[`tsun_play2_probe.py`](tsun_play2_probe.py) is the focused read-only PLAY2 probe used for protocol research when normal TSUN Local detection is insufficient.

See [PLAY2 local protocol research](../docs/PLAY2_LOCAL_RESEARCH.md).

## Other focused diagnostics

- `diagnose_device.py` — one anonymized TSUN Local protocol poll;
- `diagnose_02b0.py` — focused 02B0 diagnostics;
- `diagnose_logger_web.py` — logger web-interface diagnostics;
- `diagnose_udp_discovery.py` — privacy-safe UDP discovery test;
- `replay_diagnostic.py` — replay diagnostic captures.
