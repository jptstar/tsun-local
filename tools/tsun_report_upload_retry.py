#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Compatibility API for the canonical retrying diagnostic uploader.

Retry handling now lives directly in :mod:`tsun_report_upload` so desktop,
observer and any future caller cannot silently diverge.  This module is kept to
avoid breaking existing imports and release tooling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
import time

import tsun_report_upload as base

DEFAULT_UPLOAD_ATTEMPTS = base.DEFAULT_UPLOAD_ATTEMPTS
DEFAULT_RETRY_DELAYS = base.DEFAULT_RETRY_DELAYS
MAX_RETRY_AFTER_SECONDS = base.MAX_RETRY_AFTER_SECONDS
RETRYABLE_HTTP_STATUS = base.RETRYABLE_HTTP_STATUS

# Compatibility aliases retained for tests/tools that used the old helper API.
_is_retryable = base._is_retryable
_retry_after_seconds = base._retry_after_seconds
_retry_delay = base._retry_delay
_final_transient_message = base._final_transient_message


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
    """Delegate to the canonical uploader while preserving the former API."""
    return base.upload_file(
        path,
        consent=consent,
        tester_name=tester_name,
        declared_devices=declared_devices,
        endpoint=endpoint,
        timeout=timeout,
        user_agent=user_agent,
        attempts=attempts,
        retry_delays=retry_delays,
        sleep=sleep,
        on_retry=on_retry,
    )
