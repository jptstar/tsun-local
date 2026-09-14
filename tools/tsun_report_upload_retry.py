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

DEFAULT_UPLOAD_ATTEMPTS = 3
DEFAULT_RETRY_DELAYS = (0.75, 2.0)
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
                    f"Upload service unavailable after {attempts} attempts. "
                    f"The diagnostic report is still saved locally as {Path(path).name}. "
                    "Retry later or use the email fallback."
                ) from exc

            delay_index = min(attempt - 1, max(0, len(retry_delays) - 1))
            delay = float(retry_delays[delay_index]) if retry_delays else 0.0
            if delay > 0:
                sleep(delay)

    raise AssertionError("unreachable")
