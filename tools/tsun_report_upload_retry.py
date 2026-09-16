#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Retry wrapper for transient TSUN Local diagnostic upload failures.

The existing uploader remains the single implementation of validation, privacy
checks and HTTPS submission. This module only retries failures that are clearly
transient and leaves permanent validation / client errors untouched.
"""

from __future__ import annotations

from pathlib import Path
import socket
import time
from typing import Any, Callable, Iterable, Sequence
from urllib import error

import tsun_report_upload as base

DEFAULT_UPLOAD_ATTEMPTS = 5
DEFAULT_RETRY_DELAYS = (0.75, 2.0, 5.0, 10.0)
MAX_RETRY_AFTER_SECONDS = 30.0
RETRYABLE_HTTP_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})

# Capture the original function before the desktop entry point replaces the
# public base.upload_file symbol with the retrying wrapper below.
_ORIGINAL_UPLOAD_FILE = base.upload_file


def _is_retryable(exc: base.ReportUploadError) -> bool:
    """Return True only for transport or explicitly transient HTTP failures."""
    cause = exc.__cause__
    if isinstance(cause, error.HTTPError):
        return int(cause.code) in RETRYABLE_HTTP_STATUS
    return isinstance(cause, (error.URLError, TimeoutError, socket.timeout, OSError))


def _retry_after_seconds(exc: base.ReportUploadError) -> float | None:
    """Return a bounded numeric Retry-After value from a transient HTTP error."""
    cause = exc.__cause__
    if not isinstance(cause, error.HTTPError):
        return None
    headers = getattr(cause, "headers", None) or getattr(cause, "hdrs", None)
    if headers is None:
        return None
    try:
        raw = headers.get("Retry-After")
    except (AttributeError, TypeError):
        return None
    if raw is None:
        return None
    try:
        delay = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    if delay < 0:
        return None
    return min(delay, MAX_RETRY_AFTER_SECONDS)


def _retry_delay(
    exc: base.ReportUploadError,
    *,
    attempt: int,
    retry_delays: Sequence[float],
) -> float:
    """Choose server-requested delay when available, otherwise local backoff."""
    retry_after = _retry_after_seconds(exc)
    if retry_after is not None:
        return retry_after
    if not retry_delays:
        return 0.0
    delay_index = min(attempt - 1, len(retry_delays) - 1)
    return max(0.0, float(retry_delays[delay_index]))


def _final_transient_message(
    exc: base.ReportUploadError,
    *,
    path: Path,
    attempts: int,
) -> str:
    """Describe which upload stage failed without leaking request/report data."""
    cause = exc.__cause__
    if isinstance(cause, error.HTTPError):
        status = int(cause.code)
        if status == 429:
            stage = "Upload service reached but rate-limited (HTTP 429)"
        else:
            stage = f"Upload service reached but temporarily unavailable (HTTP {status})"
    else:
        stage = "Network/timeout: upload service could not be reached"

    return (
        f"{stage} after {attempts} attempts. "
        f"The diagnostic report is still saved locally as {Path(path).name}. "
        "Retry later or use the email fallback."
    )


def upload_file_with_retry(
    path: Path,
    *,
    consent: bool,
    tester_name: str = "",
    declared_devices: Iterable[dict[str, Any]] = (),
    endpoint: str = base.REPORT_UPLOAD_URL,
    timeout: float = base.DEFAULT_TIMEOUT,
    user_agent: str = "TSUN-Local-Diagnostic",
    attempts: int = DEFAULT_UPLOAD_ATTEMPTS,
    retry_delays: Sequence[float] = DEFAULT_RETRY_DELAYS,
    sleep: Callable[[float], None] = time.sleep,
    on_retry: Callable[[int, int, float], None] | None = None,
) -> dict[str, Any]:
    """Upload a report, retrying only failures that are safe to repeat."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")

    for attempt in range(1, attempts + 1):
        try:
            return _ORIGINAL_UPLOAD_FILE(
                path,
                consent=consent,
                tester_name=tester_name,
                declared_devices=declared_devices,
                endpoint=endpoint,
                timeout=timeout,
                user_agent=user_agent,
            )
        except base.ReportUploadError as exc:
            if not _is_retryable(exc):
                raise
            if attempt >= attempts:
                raise base.ReportUploadError(
                    _final_transient_message(exc, path=Path(path), attempts=attempts)
                ) from exc

            delay = _retry_delay(exc, attempt=attempt, retry_delays=retry_delays)
            if on_retry is not None:
                on_retry(attempt, attempts, delay)
            if delay > 0:
                sleep(delay)

    raise AssertionError("unreachable")
