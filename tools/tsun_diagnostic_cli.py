#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Full Python entry point for TSUN Local Diagnostic.

This launcher deliberately uses the same read-only extension runtime and the same
canonical upload/retry/privacy policy as the packaged Windows/macOS/Linux GUI.
The legacy single-file ``tsun_dump.py`` remains available as a minimal standard-
library fallback, but this file is the feature-parity Python diagnostic.
"""

from __future__ import annotations

import builtins
from getpass import getpass
from pathlib import Path
import sys
from typing import Any, Iterable

import tsun_diagnostic_runtime as runtime
from tsun_diagnostic_version import APP_VERSION
import tsun_dump
import tsun_report_upload as report_upload

PYTHON_UPDATE_COMPONENT = "python_full"
PYTHON_RELEASE_ASSET = "TSUN-Local-Diagnostic-Python.zip"


def _retry_notice(attempt: int, attempts: int, delay: float) -> None:
    print(
        f"Upload attempt {attempt}/{attempts} failed transiently; "
        f"retrying in {delay:g} s...",
        file=sys.stderr,
    )


def _install_canonical_upload() -> None:
    """Route CLI uploads through the same bounded retry/privacy uploader as desktop."""
    if getattr(tsun_dump, "_full_python_upload_installed", False):
        return

    def _submit_completed_reports(
        paths: list[Path],
        *,
        tester_name: str = "",
        declared_devices: Iterable[dict[str, Any]] = (),
    ) -> None:
        local_paths = [Path(path) for path in paths]
        devices = list(declared_devices)
        try:
            if devices:
                report_upload.annotate_report_files(local_paths, devices)
            print("\nSending anonymized report(s) securely to TSUN Local...")
            for path in local_paths:
                result = report_upload.upload_file(
                    path,
                    consent=True,
                    tester_name=tester_name,
                    declared_devices=devices,
                    user_agent=f"TSUN-Local-Diagnostic-Python/{APP_VERSION}",
                    on_retry=_retry_notice,
                )
                report_id = result["report_id"]
                print(f"  {path.name}: sent successfully · report ID {report_id}")
                view_url = result.get("view_url")
                if isinstance(view_url, str) and view_url.strip():
                    print(f"    Secure report link: {view_url.strip()}")
        except report_upload.ReportUploadError as exc:
            # Keep the legacy engine's public exception contract so its existing
            # delivery/error handling remains unchanged.
            raise tsun_dump.ReportUploadError(str(exc)) from exc

    tsun_dump._submit_completed_reports = _submit_completed_reports
    tsun_dump._full_python_upload_installed = True


def configure_full_runtime() -> tuple[str, ...]:
    """Install exactly the same research stages used by the packaged GUI."""
    signature = runtime.configure_dump_extensions(
        tsun_dump,
        value_prompt=lambda prompt: builtins.input(prompt),
        secret_prompt=lambda prompt: getpass(prompt),
    )
    _install_canonical_upload()
    return signature


def _check_python_package_update(*, explicit: bool) -> int | None:
    """Check the rolling full-Python component without self-modifying one module."""
    try:
        manifest = tsun_dump.fetch_update_manifest()
        update = tsun_dump.select_update_component(
            manifest,
            PYTHON_UPDATE_COMPONENT,
            APP_VERSION,
        )
    except Exception as exc:
        if explicit:
            print(f"Update check failed: {type(exc).__name__}", file=sys.stderr)
            return 1
        return None

    if update is None:
        if explicit:
            print(f"TSUN Local Diagnostic Python v{APP_VERSION} is up to date.")
        return 0 if explicit else None

    version = update.get("version") or "newer"
    asset = update.get("asset") or PYTHON_RELEASE_ASSET
    print(
        f"TSUN Local Diagnostic Python v{version} is available "
        f"({asset}). Download the latest diagnostic-latest package."
    )
    return 0 if explicit else None


def _prepare_core_argv() -> int | None:
    """Keep the multi-file bundle coherent while preserving CLI update controls."""
    if "--help" in sys.argv or "-h" in sys.argv:
        if "--no-update" not in sys.argv:
            sys.argv.insert(1, "--no-update")
        return None

    if "--check-update" in sys.argv:
        sys.argv.remove("--check-update")
        return _check_python_package_update(explicit=True)

    if "--no-update" not in sys.argv:
        _check_python_package_update(explicit=False)
        # tsun_dump's historical updater replaces only tsun_dump.py.  The full
        # Python distribution is versioned as one coherent package instead.
        sys.argv.insert(1, "--no-update")
    return None


def main() -> int:
    configure_full_runtime()
    update_result = _prepare_core_argv()
    if update_result is not None:
        return update_result
    return int(tsun_dump.main())


if __name__ == "__main__":
    raise SystemExit(main())
