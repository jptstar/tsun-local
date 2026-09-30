#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Windows desktop entry point for TSUN Local Diagnostic.

The supported packaged GUI is the Windows executable. Non-Windows users use the
full Python diagnostic package. Source-level platform helpers remain limited to
profile storage and opening folders; the read-only engine, extension composition
and report-upload flow stay shared.
"""

from __future__ import annotations

import builtins
import os
from pathlib import Path
import platform
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

import tsun_diagnostic_runtime as runtime
import tsun_dump
import tsun_diagnostic_reports as ui
from tsun_diagnostic_version import APP_VERSION

# Keep the public compatibility shape used by existing tests and helper code:
# `previous` remains the profile/persistence layer while `ui` is the
# report-link layer inherited by the final application class below.
previous = ui.previous

APP_NAME = ui.APP_NAME
MAX_DEVICE_ROWS = ui.MAX_DEVICE_ROWS
PROJECT_URL = ui.PROJECT_URL
COPYRIGHT_TEXT = ui.COPYRIGHT_TEXT
SUNOLOGY_PLAY2_MODEL = ui.SUNOLOGY_PLAY2_MODEL
PROFILE_DIR_NAME = previous.PROFILE_DIR_NAME
PROFILE_FILE_NAME = previous.PROFILE_FILE_NAME

# Preserve the helpers expected by tests and by external tooling.
load_upload_profile = previous.load_upload_profile
save_upload_profile = previous.save_upload_profile
filter_microinverter_models = previous.filter_microinverter_models

# Keep every inherited layer on one visible GUI version.
ui.APP_VERSION = APP_VERSION
previous.APP_VERSION = APP_VERSION
previous.legacy.APP_VERSION = APP_VERSION
previous.legacy.base.APP_VERSION = APP_VERSION
previous.legacy.upload_app.APP_VERSION = APP_VERSION

# Make the successful upload stages explicit without exposing the private reports
# repository. A Worker receipt with a report ID is only rendered after the server
# accepted the report and returned its creation receipt.
previous.legacy.upload_app._TEXT["fr"].update(
    {
        "upload_service_ok": "✓ Service d’envoi joignable",
        "upload_storage_ok": "✓ Rapport accepté et enregistré côté serveur",
        "upload_report_id": "✓ Report ID : {report_id}",
    }
)
previous.legacy.upload_app._TEXT["en"].update(
    {
        "upload_service_ok": "✓ Upload service reachable",
        "upload_storage_ok": "✓ Report accepted and stored by the server",
        "upload_report_id": "✓ Report ID: {report_id}",
    }
)

# The inherited GUI routes interactive CLI prompts through tkinter.simpledialog.
# Mark Local Key prompts so only that secret field is masked; ordinary diagnostic
# questions keep their existing behavior. The key remains in process memory only.
if not hasattr(simpledialog, "_tsun_local_original_askstring"):
    simpledialog._tsun_local_original_askstring = simpledialog.askstring  # type: ignore[attr-defined]


def _privacy_aware_askstring(title: str, prompt: str, *args, **kwargs):
    original = simpledialog._tsun_local_original_askstring  # type: ignore[attr-defined]
    if isinstance(prompt, str) and prompt.startswith(runtime.SECRET_PROMPT_PREFIX):
        prompt = prompt[len(runtime.SECRET_PROMPT_PREFIX) :]
        kwargs.setdefault("show", "*")
    return original(title, prompt, *args, **kwargs)


simpledialog.askstring = _privacy_aware_askstring


def _configure_diagnostic_runtime() -> tuple[str, ...]:
    """Compose all desktop-only diagnostic extensions in one tested order."""
    # Lambdas resolve builtins.input at call time, after the inherited worker has
    # redirected it to the GUI dialog bridge. No secret enters argv/env/profile.
    return runtime.configure_dump_extensions(
        tsun_dump,
        value_prompt=lambda prompt: builtins.input(prompt),
        secret_prompt=lambda prompt: builtins.input(
            runtime.SECRET_PROMPT_PREFIX + prompt
        ),
    )


UPDATE_COMPONENT_WINDOWS = "windows_gui"
ASSET_WINDOWS = "TSUN-Local-Diagnostic.exe"



def platform_update_component(
    *, system: str | None = None, machine: str | None = None
) -> str | None:
    """Return the rolling-release manifest component for this packaged GUI."""
    current_system = (system or platform.system() or "").strip().lower()
    if current_system == "windows":
        return UPDATE_COMPONENT_WINDOWS
    return None


def platform_release_asset(
    *, system: str | None = None, machine: str | None = None
) -> str | None:
    component = platform_update_component(system=system, machine=machine)
    return ASSET_WINDOWS if component == UPDATE_COMPONENT_WINDOWS else None


_original_profile_candidates = previous._profile_candidates


def _platform_profile_candidates() -> list[Path]:
    """Use durable per-user config locations while keeping migration fallbacks."""
    if os.name == "nt":
        return _original_profile_candidates()

    home = Path.home()
    if sys.platform == "darwin":
        primary = home / "Library" / "Application Support" / PROFILE_DIR_NAME / PROFILE_FILE_NAME
        legacy = home / ".config" / PROFILE_DIR_NAME / PROFILE_FILE_NAME
        return [primary, legacy]

    root = Path(os.environ.get("XDG_CONFIG_HOME") or (home / ".config"))
    return [root / PROFILE_DIR_NAME / PROFILE_FILE_NAME]


# The 1.5.8 load/save functions resolve `_profile_candidates` dynamically, so
# replacing this one function upgrades storage without duplicating their logic.
previous._profile_candidates = _platform_profile_candidates
previous.legacy.load_upload_profile = previous.load_upload_profile
previous.legacy.save_upload_profile = previous.save_upload_profile


class CleanDiagnosticApp(ui.CleanDiagnosticApp):
    """Desktop UI with minimal OS-specific integration."""

    def _render_report_links(self, host: tk.Frame, reports: list[tuple[str, str]]) -> None:
        """Render the normal receipt links plus explicit upload-stage confirmation."""
        super()._render_report_links(host, reports)
        try:
            children = host.winfo_children()
            if not children:
                return

            base = previous.legacy.base
            status = tk.Frame(host, bg=base._SOFT_GREEN)
            pack_options: dict[str, object] = {
                "fill": "x",
                "padx": 10,
                "pady": (0, 7),
            }
            if len(children) > 1:
                pack_options["before"] = children[1]
            status.pack(**pack_options)

            for text in (
                self.u["upload_service_ok"],
                self.u["upload_storage_ok"],
            ):
                tk.Label(
                    status,
                    text=text,
                    bg=base._SOFT_GREEN,
                    fg=base._SUCCESS,
                    font=("Segoe UI", 8, "bold"),
                    anchor="w",
                ).pack(fill="x")

            for report_id, _url in reports:
                tk.Label(
                    status,
                    text=self.u["upload_report_id"].format(report_id=report_id),
                    bg=base._SOFT_GREEN,
                    fg=base._TEXT_COLOR,
                    font=("Segoe UI", 8, "bold"),
                    anchor="w",
                ).pack(fill="x", pady=(2, 0))
        except tk.TclError:
            pass

    def _open_folder(self) -> None:
        folder = Path(self.output_dir.get()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)], close_fds=True)
            else:
                subprocess.Popen(
                    ["xdg-open", str(folder)],
                    close_fds=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except (OSError, FileNotFoundError) as exc:
            messagebox.showinfo(APP_NAME, f"{folder}\n\n{exc}")

def main() -> int:
    internal_result = previous.legacy.base._internal_update_mode()
    if internal_result is not None:
        return internal_result
    _configure_diagnostic_runtime()
    root = tk.Tk()
    CleanDiagnosticApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
