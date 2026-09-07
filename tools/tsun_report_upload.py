#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Privacy-safe upload client for TSUN Local diagnostic reports.

The client contains no GitHub credential. It sends one already-anonymized
local diagnostic JSON to the public Cloudflare upload endpoint only after
explicit user consent. The server performs a second validation pass before
writing the report into the private reports repository.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import socket
from typing import Any, Iterable
from urllib import error, request

REPORT_UPLOAD_URL = "https://tsun-local-reports-uploader.jp-810.workers.dev/report"
MAX_REPORT_BYTES = 524288
DEFAULT_TIMEOUT = 20.0

FORBIDDEN_KEYS = frozenset(
    {
        "monitor_sn",
        "monitor_serial",
        "serial_number",
        "logger_ip",
        "ip_address",
        "mac",
        "mac_address",
        "ssid",
        "password",
        "wifi_password",
        "token",
        "access_token",
        "refresh_token",
        "email",
        "e_mail",
    }
)

_DEVICE_SUFFIX_RE = re.compile(r"^(?P<model>.+?)\s+[xX×]\s*(?P<quantity>\d{1,2})$")
_DEVICE_PREFIX_RE = re.compile(r"^(?P<quantity>\d{1,2})\s*[xX×]\s*(?P<model>.+)$")


class ReportUploadError(RuntimeError):
    """Raised when a report cannot be safely submitted."""


def _assert_string(value: str, name: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ReportUploadError(f"{name} must be text")
    cleaned = value.strip()
    if len(cleaned) > max_length:
        raise ReportUploadError(f"{name} is too long")
    return cleaned


def _find_forbidden_key(value: Any, path: str = "$", depth: int = 0) -> str | None:
    if depth > 40:
        raise ReportUploadError("diagnostic nesting is too deep")
    if isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_forbidden_key(child, f"{path}[{index}]", depth + 1)
            if found:
                return found
        return None
    if not isinstance(value, dict):
        return None
    for key, child in value.items():
        key_text = str(key)
        if key_text.lower() in FORBIDDEN_KEYS:
            return f"{path}.{key_text}"
        found = _find_forbidden_key(child, f"{path}.{key_text}", depth + 1)
        if found:
            return found
    return None


def validate_diagnostic(diagnostic: Any) -> dict[str, Any]:
    """Validate the local diagnostic before any network transmission occurs."""
    if not isinstance(diagnostic, dict):
        raise ReportUploadError("diagnostic JSON must contain an object")
    forbidden = _find_forbidden_key(diagnostic)
    if forbidden:
        raise ReportUploadError(f"diagnostic contains a forbidden privacy field: {forbidden}")
    return diagnostic


def load_diagnostic(path: Path) -> dict[str, Any]:
    """Load one local diagnostic and apply the local privacy gate."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReportUploadError(f"cannot read diagnostic file: {path.name}") from exc
    if size <= 0:
        raise ReportUploadError(f"diagnostic file is empty: {path.name}")
    if size > MAX_REPORT_BYTES:
        raise ReportUploadError(f"diagnostic file is too large: {path.name}")
    try:
        diagnostic = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ReportUploadError(f"diagnostic file is not valid JSON: {path.name}") from exc
    return validate_diagnostic(diagnostic)


def parse_declared_devices(text: str) -> list[dict[str, Any]]:
    """Parse an optional human-entered inverter inventory.

    Accepted examples::

        TSOL-MX500
        TSOL-MP3000 x2
        2x TSOL-MS800

    Duplicate model names are merged case-insensitively while preserving the
    spelling from the first line.
    """
    if not isinstance(text, str):
        raise ReportUploadError("device list must be text")

    merged: dict[str, dict[str, Any]] = {}
    for raw_line in text.replace(";", "\n").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        model = line
        quantity = 1
        match = _DEVICE_SUFFIX_RE.match(line) or _DEVICE_PREFIX_RE.match(line)
        if match:
            model = match.group("model").strip()
            quantity = int(match.group("quantity"))

        model = _assert_string(model, "device model", 80)
        if not model:
            raise ReportUploadError("device model cannot be empty")
        if not 1 <= quantity <= 99:
            raise ReportUploadError("device quantity must be between 1 and 99")

        key = model.casefold()
        if key in merged:
            new_quantity = int(merged[key]["quantity"]) + quantity
            if new_quantity > 99:
                raise ReportUploadError(f"device quantity exceeds 99 for {model}")
            merged[key]["quantity"] = new_quantity
        else:
            if len(merged) >= 50:
                raise ReportUploadError("too many different device models")
            merged[key] = {"model": model, "quantity": quantity}

    return sorted(merged.values(), key=lambda item: str(item["model"]).casefold())


def build_payload(
    diagnostic: dict[str, Any],
    *,
    consent: bool,
    tester_name: str = "",
    declared_devices: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """Build the exact schema accepted by the report upload Worker."""
    if consent is not True:
        raise ReportUploadError("explicit consent is required")
    diagnostic = validate_diagnostic(diagnostic)
    name = _assert_string(tester_name, "tester name", 80)

    devices: list[dict[str, Any]] = []
    for index, item in enumerate(declared_devices):
        if not isinstance(item, dict):
            raise ReportUploadError(f"declared device {index + 1} is invalid")
        model = _assert_string(str(item.get("model", "")), "device model", 80)
        if not model:
            raise ReportUploadError("device model cannot be empty")
        try:
            quantity = int(item.get("quantity", 1))
        except (TypeError, ValueError) as exc:
            raise ReportUploadError("device quantity must be an integer") from exc
        if not 1 <= quantity <= 99:
            raise ReportUploadError("device quantity must be between 1 and 99")
        devices.append({"model": model, "quantity": quantity})
    if len(devices) > 50:
        raise ReportUploadError("too many different device models")

    return {
        "schema_version": 1,
        "consent": True,
        "tester_profile": {
            "name": name,
            "declared_devices": devices,
        },
        "diagnostic": diagnostic,
    }


def _server_error_message(exc: error.HTTPError) -> str:
    try:
        raw = exc.read(4096)
        body = json.loads(raw.decode("utf-8", errors="replace"))
        message = body.get("error") if isinstance(body, dict) else None
    except (OSError, ValueError, UnicodeError):
        message = None
    if isinstance(message, str) and message.strip():
        return message.strip()
    return f"HTTP {exc.code}"


def upload_diagnostic(
    diagnostic: dict[str, Any],
    *,
    consent: bool,
    tester_name: str = "",
    declared_devices: Iterable[dict[str, Any]] = (),
    endpoint: str = REPORT_UPLOAD_URL,
    timeout: float = DEFAULT_TIMEOUT,
    user_agent: str = "TSUN-Local-Diagnostic",
) -> dict[str, Any]:
    """Submit one diagnostic to the upload Worker and return its receipt."""
    payload = build_payload(
        diagnostic,
        consent=consent,
        tester_name=tester_name,
        declared_devices=declared_devices,
    )
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(body) > MAX_REPORT_BYTES:
        raise ReportUploadError("report is too large after adding upload metadata")

    req = request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": user_agent,
        },
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_body = response.read(MAX_REPORT_BYTES + 1)
    except error.HTTPError as exc:
        raise ReportUploadError(f"upload rejected: {_server_error_message(exc)}") from exc
    except (error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        raise ReportUploadError("upload service is unreachable") from exc

    if len(response_body) > MAX_REPORT_BYTES:
        raise ReportUploadError("upload service returned an invalid response")
    try:
        result = json.loads(response_body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReportUploadError("upload service returned invalid JSON") from exc
    if not isinstance(result, dict) or result.get("ok") is not True:
        message = result.get("error") if isinstance(result, dict) else None
        raise ReportUploadError(str(message or "upload failed"))
    if not isinstance(result.get("report_id"), str):
        raise ReportUploadError("upload service did not return a report ID")
    return result


def upload_file(
    path: Path,
    *,
    consent: bool,
    tester_name: str = "",
    declared_devices: Iterable[dict[str, Any]] = (),
    endpoint: str = REPORT_UPLOAD_URL,
    timeout: float = DEFAULT_TIMEOUT,
    user_agent: str = "TSUN-Local-Diagnostic",
) -> dict[str, Any]:
    """Load, privacy-check and upload one local JSON diagnostic."""
    diagnostic = load_diagnostic(path)
    return upload_diagnostic(
        diagnostic,
        consent=consent,
        tester_name=tester_name,
        declared_devices=declared_devices,
        endpoint=endpoint,
        timeout=timeout,
        user_agent=user_agent,
    )
