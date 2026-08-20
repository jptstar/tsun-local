# TSUN Local tools

Diagnostic and validation utilities for TSUN Local.

## Hardware validation dump

Use [`tsun_dump.py`](tsun_dump.py) to create a standardized, privacy-safe, strictly read-only hardware dump for protocol **1511**, **02B0** or **1097**.

```bash
python tools/tsun_dump.py
```

The tool tries local UDP discovery first. IP address and Monitor SN are requested only when automatic discovery cannot resolve them.

For the complete safety model, capture ranges, full mode, snapshots and before/after comparison, see [Hardware Validation Dump Tool](../docs/HARDWARE_DUMP.md).

## Existing focused diagnostics

- `diagnose_device.py` — one anonymized TSUN Local protocol poll;
- `diagnose_02b0.py` — focused 02B0 diagnostics;
- `diagnose_logger_web.py` — logger web-interface diagnostics;
- `diagnose_udp_discovery.py` — privacy-safe UDP discovery test;
- `replay_diagnostic.py` — replay diagnostic captures.
