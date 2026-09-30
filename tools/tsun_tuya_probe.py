#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Authenticated, strictly read-only Tuya LAN probe for TSUN Local Diagnostic.

This module extends the existing transport-only Tuya candidate capture. Credentials
are requested interactively and kept only in process memory. The only device
application operation used is TinyTuya ``status()``; no configuration/control
method is called. Reports contain sanitized DPS observations and never contain the
Device ID or Local Key.
"""

from __future__ import annotations

import builtins
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import time
from typing import Any, Callable

PROBE_VERSION = "1.0.0"
SECRET_PROMPT_PREFIX = "[[TSUN_LOCAL_SECRET]] "
SUPPORTED_TUYA_VERSIONS = (3.5, 3.4, 3.3, 3.2, 3.1)
MAX_DPS_ITEMS = 256
MAX_COMPLEX_VALUE_BYTES = 4096
_DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{6,64}$")

ValuePrompt = Callable[[str], str]
SecretPrompt = Callable[[str], str]


def _load_tinytuya() -> Any:
    """Import TinyTuya lazily so the standalone stdlib dumper still imports."""
    import tinytuya  # type: ignore[import-not-found]

    return tinytuya


def _library_version(backend: Any) -> str | None:
    value = getattr(backend, "__version__", None)
    if isinstance(value, str) and value.strip():
        return value.strip()[:32]
    return None


def _clean_device_id(value: str) -> str | None:
    candidate = value.strip()
    return candidate if _DEVICE_ID_RE.fullmatch(candidate) else None


def _clean_local_key(value: str) -> str | None:
    candidate = value.strip()
    try:
        encoded = candidate.encode("utf-8")
    except UnicodeError:
        return None
    return candidate if len(encoded) == 16 else None


def _fingerprint_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _json_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=lambda item: repr(type(item).__name__),
        ).encode("utf-8", errors="replace")
    except (TypeError, ValueError, OverflowError):
        encoded = repr(type(value).__name__).encode("ascii", errors="replace")
    return encoded[:MAX_COMPLEX_VALUE_BYTES]


def _sanitize_dps_value(value: Any) -> Any:
    """Keep useful numeric state while fingerprinting potentially identifying text."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return {"type": "float", "value": "non_finite"}
    if isinstance(value, str):
        raw = value.encode("utf-8", errors="replace")
        return {
            "type": "string",
            "length": len(value),
            "sha256": _fingerprint_bytes(raw),
        }
    if isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
        return {
            "type": "bytes",
            "length": len(raw),
            "sha256": _fingerprint_bytes(raw),
        }

    raw = _json_bytes(value)
    length = len(value) if isinstance(value, (list, tuple, dict, set)) else None
    result: dict[str, Any] = {
        "type": type(value).__name__[:32],
        "sha256": _fingerprint_bytes(raw),
    }
    if length is not None:
        result["length"] = int(length)
    return result


def _extract_dps(status: Any) -> dict[str, Any] | None:
    if not isinstance(status, dict):
        return None
    dps = status.get("dps")
    if not isinstance(dps, dict):
        data = status.get("data")
        if isinstance(data, dict):
            dps = data.get("dps")
    if not isinstance(dps, dict):
        return None

    result: dict[str, Any] = {}
    for key, value in list(dps.items())[:MAX_DPS_ITEMS]:
        key_text = str(key).strip()
        if not key_text or len(key_text) > 32:
            continue
        result[key_text] = _sanitize_dps_value(value)
    return result


def _safe_error_record(result: Any = None, exc: BaseException | None = None) -> dict[str, Any]:
    """Return diagnostic failure metadata without retaining backend messages/payloads."""
    if exc is not None:
        return {
            "result": "exception",
            "error_type": type(exc).__name__[:80],
        }
    if isinstance(result, dict):
        code = result.get("Err")
        if isinstance(code, (str, int)):
            return {"result": "error", "error_code": str(code)[:16]}
    return {"result": "no_dps"}


def _new_device(
    backend: Any,
    device_identifier: str,
    host: str,
    local_key: str,
    version: float,
    timeout: float,
) -> Any:
    """Create one bounded TinyTuya device object without issuing a command."""
    device = backend.Device(
        device_identifier,
        host,
        local_key,
        version=version,
        persist=False,
        connection_timeout=timeout,
        connection_retry_limit=1,
        connection_retry_delay=0,
    )
    # Keep retries tightly bounded even if a backend version ignores constructor
    # compatibility arguments. These methods only affect the local TCP client.
    for method_name, argument in (
        ("set_socketPersistent", False),
        ("set_socketRetryLimit", 1),
        ("set_socketRetryDelay", 0),
        ("set_socketTimeout", timeout),
        ("set_retry", False),
    ):
        method = getattr(device, method_name, None)
        if callable(method):
            method(argument)
    return device


def _attempt_version(
    backend: Any,
    device_identifier: str,
    host: str,
    local_key: str,
    version: float,
    timeout: float,
) -> tuple[dict[str, Any], dict[str, Any] | None, Any | None]:
    started = time.monotonic()
    try:
        device = _new_device(
            backend,
            device_identifier,
            host,
            local_key,
            version,
            timeout,
        )
        status = device.status()
    except Exception as exc:  # Backend boundary: details are intentionally discarded.
        record = _safe_error_record(exc=exc)
        record["latency_ms"] = round((time.monotonic() - started) * 1000, 1)
        return record, None, None

    dps = _extract_dps(status)
    if dps is None:
        record = _safe_error_record(result=status)
        record["latency_ms"] = round((time.monotonic() - started) * 1000, 1)
        return record, None, None

    return (
        {
            "result": "success",
            "latency_ms": round((time.monotonic() - started) * 1000, 1),
            "dps_count": len(dps),
        },
        dps,
        device,
    )


def _dps_analysis(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    maps = [item.get("dps", {}) for item in snapshots if isinstance(item.get("dps"), dict)]
    if not maps:
        return {"keys": [], "stable": [], "changing": [], "incomplete": []}
    keys = sorted(set().union(*(mapping.keys() for mapping in maps)), key=str)
    stable: list[str] = []
    changing: list[str] = []
    incomplete: list[str] = []
    for key in keys:
        if not all(key in mapping for mapping in maps):
            incomplete.append(key)
            continue
        fingerprints = [
            hashlib.sha256(_json_bytes(mapping[key])).hexdigest() for mapping in maps
        ]
        (stable if len(set(fingerprints)) == 1 else changing).append(key)
    return {
        "keys": keys,
        "stable": stable,
        "changing": changing,
        "incomplete": incomplete,
    }


def extend_tuya_capture(
    document: dict[str, Any],
    args: Any,
    host: str,
    *,
    value_prompt: ValuePrompt | None = None,
    secret_prompt: SecretPrompt | None = None,
    backend: Any | None = None,
) -> dict[str, Any]:
    """Attempt a bounded authenticated status read and enrich one Tuya report."""
    tuya = document.get("tuya_lan")
    metadata = document.get("metadata")
    if not isinstance(tuya, dict) or not isinstance(metadata, dict):
        return document
    if not bool(tuya.get("candidate_confirmed")):
        return document

    tuya["authenticated_probe_version"] = PROBE_VERSION
    tuya["authenticated_read_available"] = True
    tuya["credentials_storage"] = "memory_only"
    tuya["device_identifier_stored"] = False
    tuya["local_key_stored"] = False
    tuya["local_key_uploaded"] = False

    if backend is None:
        try:
            backend = _load_tinytuya()
        except (ImportError, ModuleNotFoundError):
            tuya["authenticated_read_available"] = False
            tuya["status_read_blocked_by"] = "tuya_backend_unavailable"
            tuya["status_read_reason"] = (
                "Authenticated Tuya probing is unavailable in this package."
            )
            return document

    tuya["library"] = "TinyTuya"
    library_version = _library_version(backend)
    if library_version is not None:
        tuya["library_version"] = library_version

    value_prompt = value_prompt or builtins.input
    secret_prompt = secret_prompt or builtins.input
    try:
        entered_id = value_prompt(
            "Tuya Device ID (used only in memory; Enter to skip authenticated read): "
        )
    except (EOFError, KeyboardInterrupt):
        entered_id = ""
    if not entered_id.strip():
        tuya["device_id_requested"] = True
        tuya["local_key_requested"] = False
        tuya["status_read_blocked_by"] = "credentials_skipped"
        tuya["status_read_reason"] = "Authenticated Tuya status read was skipped by the user."
        return document

    device_identifier = _clean_device_id(entered_id)
    tuya["device_id_requested"] = True
    if device_identifier is None:
        tuya["local_key_requested"] = False
        tuya["status_read_blocked_by"] = "invalid_device_identifier"
        tuya["status_read_reason"] = "The supplied Tuya Device ID format was invalid."
        return document

    try:
        entered_key = secret_prompt(
            "Tuya Local Key (16 bytes; used only in memory and never saved/uploaded): "
        )
    except (EOFError, KeyboardInterrupt):
        entered_key = ""
    tuya["local_key_requested"] = True
    local_key = _clean_local_key(entered_key)
    # Drop the original prompt strings as early as practical. Python strings cannot
    # be reliably zeroized, but no credential is persisted in the report/profile.
    entered_id = ""
    entered_key = ""
    if local_key is None:
        tuya["status_read_blocked_by"] = "invalid_local_key"
        tuya["status_read_reason"] = "The supplied Tuya Local Key must be exactly 16 UTF-8 bytes."
        return document

    timeout = min(max(float(getattr(args, "timeout", 3.0)), 0.5), 4.0)
    attempts: list[dict[str, Any]] = []
    selected_version: float | None = None
    first_dps: dict[str, Any] | None = None
    selected_device: Any | None = None

    for version in SUPPORTED_TUYA_VERSIONS:
        record, dps, device = _attempt_version(
            backend,
            device_identifier,
            host,
            local_key,
            version,
            timeout,
        )
        attempts.append({"version": f"{version:.1f}", **record})
        if dps is not None:
            selected_version = version
            first_dps = dps
            selected_device = device
            break

    tuya["status_read_attempted"] = True
    tuya["application_payload_sent"] = True
    tuya["version_attempts"] = attempts
    tuya["configuration_write_performed"] = False
    tuya["control_command_sent"] = False

    if selected_version is None or first_dps is None:
        tuya["status_read_success"] = False
        tuya["status_read_blocked_by"] = "authentication_or_version_failed"
        tuya["status_read_reason"] = (
            "No supported Tuya LAN version returned DPS with the supplied in-memory credentials."
        )
        metadata["capture_limitation"] = "tuya_authenticated_status_failed"
        metadata["measurements_available"] = False
        return document

    snapshots: list[dict[str, Any]] = [
        {
            "index": 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "dps": first_dps,
        }
    ]
    wanted = max(1, min(int(getattr(args, "snapshots", 1)), 5))
    interval = max(0.0, min(float(getattr(args, "interval", 0.0)), 3.0))
    device = selected_device
    for index in range(2, wanted + 1):
        if interval:
            time.sleep(interval)
        try:
            status = device.status() if device is not None else None
        except Exception:
            continue
        dps = _extract_dps(status)
        if dps is None:
            continue
        snapshots.append(
            {
                "index": index,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "dps": dps,
            }
        )

    tuya["protocol_version"] = f"{selected_version:.1f}"
    tuya["status_read_success"] = True
    tuya["status_read_blocked_by"] = None
    tuya["status_read_reason"] = None
    tuya["dps_snapshots"] = snapshots
    tuya["dps_analysis"] = _dps_analysis(snapshots)
    tuya["raw_string_values_in_output"] = False
    tuya["string_and_complex_values_fingerprinted"] = True

    metadata["capture_status"] = "success"
    metadata["protocol_validation_status"] = "authenticated_read"
    metadata["capture_limitation"] = None
    metadata["measurements_available"] = bool(first_dps)
    metadata["requires_local_key_for_status"] = True
    privacy = metadata.setdefault("privacy", {})
    if isinstance(privacy, dict):
        privacy["tuya_credentials_memory_only"] = True
        privacy["tuya_raw_string_values_in_output"] = False
        privacy["tuya_complex_values_fingerprinted"] = True

    document["capture_summary"]["snapshots"] = len(snapshots)
    document["capture_summary"]["coherent_snapshots"] = len(snapshots)
    document["capture_summary"]["unique_raw_registers"] = 0
    return document


def install(
    tsun_dump_module: Any,
    *,
    value_prompt: ValuePrompt | None = None,
    secret_prompt: SecretPrompt | None = None,
) -> None:
    """Install the authenticated Tuya extension onto the existing dump engine."""
    if getattr(tsun_dump_module, "_authenticated_tuya_probe_installed", False):
        return
    original = tsun_dump_module.capture_tuya_candidate

    def wrapped(args: Any, host: str, discovery: dict[str, Any]) -> dict[str, Any]:
        document = original(args, host, discovery)
        return extend_tuya_capture(
            document,
            args,
            host,
            value_prompt=value_prompt,
            secret_prompt=secret_prompt,
        )

    tsun_dump_module.capture_tuya_candidate = wrapped
    tsun_dump_module._authenticated_tuya_probe_installed = True
