# TSUN Local tools

This directory contains the supported diagnostic entry points plus focused field and research utilities used to validate TSUN hardware safely.

All inverter/protocol probes in this directory are designed for **read-only diagnostics** unless a tool explicitly documents a different action.

## Supported diagnostic entry points

### Windows desktop diagnostic

The supported packaged GUI is built from [`tsun_diagnostic.py`](tsun_diagnostic.py) and published as:

- [TSUN-Local-Diagnostic.exe](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe)
- [SHA-256 checksum](https://github.com/jptstar/tsun-local/releases/download/diagnostic-latest/TSUN-Local-Diagnostic.exe.sha256)

The historical Windows release URL remains stable for links already published in issues, forum posts and documentation.

### Full Python diagnostic

[`tsun_diagnostic_cli.py`](tsun_diagnostic_cli.py) is the supported non-Windows/full-Python entry point. The rolling release contains the complete source bundle and its pinned dependency list.

Run from the source bundle with Python 3.10+:

```bash
python tsun_diagnostic_cli.py --full
```

The full Python package uses the same read-only engine, runtime extension order, privacy validation and report uploader as the Windows diagnostic.

### Single-file compatibility diagnostic

[`tsun_dump.py`](tsun_dump.py) remains available as the standalone standard-library fallback and compatibility path:

```bash
python3 tsun_dump.py --full
```

It performs local discovery first, requests an IP address or Monitor SN only when needed, and excludes those values from the shareable diagnostic JSON.

For capture ranges, privacy rules and evidence handling, see the [Hardware Validation Dump Tool guide](../docs/HARDWARE_DUMP.md).

## Field and research utilities

These tools are intentionally more focused than the normal diagnostic and are used when a specific protocol, logger or hardware family needs additional evidence.

- [`tsun_observe_02b0.py`](tsun_observe_02b0.py) — long-running 02B0 stability observer used to distinguish TCP reachability from incomplete/invalid Modbus replies.
- [`tsun_play2_probe.py`](tsun_play2_probe.py) — standalone PLAY2/MX investigation tool combining local discovery and bounded read-only protocol hypotheses.
- [`tsun_1097_research_probe.py`](tsun_1097_research_probe.py) — targeted GEN4/1097 research fallback.
- [`tsun_1097_transport_extension.py`](tsun_1097_transport_extension.py) — transport-enrichment stage shared by the full diagnostic runtime.
- [`tsun_tuya_probe.py`](tsun_tuya_probe.py) — authenticated read-only Tuya LAN diagnostic path when a Local Key is supplied locally.
- [`tsun_ota_probe.py`](tsun_ota_probe.py) — passive OTA/network capture helper for research.
- [`dc1000_3026_readonly_probe.py`](dc1000_3026_readonly_probe.py) — focused read-only 3026/DC1000 investigation.

The [long-running 02B0 observation guide](../docs/guides/02B0_OBSERVATION.md) documents the observer workflow.

## Focused diagnostics

Small standalone helpers remain available for narrow troubleshooting tasks:

- [`diagnose_device.py`](diagnose_device.py) — one anonymized TSUN Local protocol poll.
- [`diagnose_02b0.py`](diagnose_02b0.py) — focused 02B0 diagnostics.
- [`diagnose_logger_web.py`](diagnose_logger_web.py) — logger web-interface diagnostics.
- [`diagnose_udp_discovery.py`](diagnose_udp_discovery.py) — privacy-safe UDP discovery test.
- [`replay_diagnostic.py`](replay_diagnostic.py) — replay previously captured diagnostic data without talking to live hardware.

## Internal diagnostic modules

The remaining `tsun_diagnostic_*.py` and `tsun_report_*.py` files are implementation modules used by the supported entry points. They are **not separate user-facing diagnostic programs**.

In particular:

- `tsun_diagnostic_runtime.py` owns the ordered optional diagnostic extensions;
- `tsun_diagnostic_version.py` owns the shared diagnostic version;
- `tsun_report_upload.py` owns the canonical privacy-safe uploader;
- `tsun_report_upload_retry.py` and `tsun_report_model_assignment.py` are compatibility shims for older imports.

## Repository maintenance

[`update_download_stats.py`](update_download_stats.py) updates the generated GitHub Release download statistics under `docs/stats/`. It is repository maintenance code, not an inverter diagnostic.
