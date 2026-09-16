#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Stable cross-platform entry point for TSUN Local Diagnostic.

The same Tk interface is packaged for Windows, macOS and Linux. Platform-specific
code here is intentionally limited to profile storage, opening folders and
selecting the correct rolling-release update component. The read-only diagnostic
engine, extension composition and report-upload flow remain shared.
"""

from __future__ import annotations

import builtins
import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

import tsun_diagnostic_runtime as runtime
import tsun_dump
import tsun_diagnostic_desktop_v159 as ui

# Keep the public compatibility shape used by existing tests and helper code:
# `previous` remains the 1.5.8 UI/persistence layer while `ui` is the 1.5.10
# report-link layer inherited by the final application class below.
previous = ui.previous

APP_NAME = ui.APP_NAME
APP_VERSION = "1.5.21"
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
UPDATE_COMPONENT_MACOS_ARM64 = "macos_arm64_gui"
UPDATE_COMPONENT_MACOS_X86_64 = "macos_x86_64_gui"
UPDATE_COMPONENT_LINUX_X86_64 = "linux_x86_64_gui"
UPDATE_COMPONENT_LINUX_ARM64 = "linux_arm64_gui"

ASSET_WINDOWS = "TSUN-Local-Diagnostic.exe"
ASSET_MACOS_ARM64 = "TSUN-Local-Diagnostic-macOS-arm64.zip"
ASSET_MACOS_X86_64 = "TSUN-Local-Diagnostic-macOS-x86_64.zip"
ASSET_LINUX_X86_64 = "TSUN-Local-Diagnostic-Linux-x86_64"
ASSET_LINUX_ARM64 = "TSUN-Local-Diagnostic-Linux-arm64"


def _normalized_machine(value: str | None = None) -> str:
    machine = (value or platform.machine() or "").strip().lower()
    if machine in {"amd64", "x64", "x86-64"}:
        return "x86_64"
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    return machine


def platform_update_component(
    *, system: str | None = None, machine: str | None = None
) -> str | None:
    """Return the rolling-release manifest component for this packaged GUI."""
    current_system = (system or platform.system() or "").strip().lower()
    current_machine = _normalized_machine(machine)
    if current_system == "windows":
        return UPDATE_COMPONENT_WINDOWS
    if current_system == "darwin":
        if current_machine == "arm64":
            return UPDATE_COMPONENT_MACOS_ARM64
        if current_machine == "x86_64":
            return UPDATE_COMPONENT_MACOS_X86_64
    if current_system == "linux":
        if current_machine == "arm64":
            return UPDATE_COMPONENT_LINUX_ARM64
        if current_machine == "x86_64":
            return UPDATE_COMPONENT_LINUX_X86_64
    return None


def platform_release_asset(
    *, system: str | None = None, machine: str | None = None
) -> str | None:
    component = platform_update_component(system=system, machine=machine)
    return {
        UPDATE_COMPONENT_WINDOWS: ASSET_WINDOWS,
        UPDATE_COMPONENT_MACOS_ARM64: ASSET_MACOS_ARM64,
        UPDATE_COMPONENT_MACOS_X86_64: ASSET_MACOS_X86_64,
        UPDATE_COMPONENT_LINUX_X86_64: ASSET_LINUX_X86_64,
        UPDATE_COMPONENT_LINUX_ARM64: ASSET_LINUX_ARM64,
    }.get(component)


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
    """Same UI on all desktop platforms with minimal OS-specific integration."""

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

    def _start_update_check(self) -> None:
        """Use the GUI package component on macOS/Linux; keep Windows auto-update."""
        if os.name == "nt":
            super()._start_update_check()
            return

        if "--no-update" in sys.argv:
            self.update_busy = False
            self.update_status.set(self.t["update_disabled"])
            try:
                self.update_label.configure(fg=previous.legacy.base._MUTED)
            except tk.TclError:
                pass
            return

        component = platform_update_component()
        if component is None:
            # Unsupported packaging architecture: retain the safe legacy dumper
            # update check rather than pretending the GUI itself can be updated.
            super()._start_update_check()
            return

        self.update_busy = True
        self.update_status.set(self.t["update_checking"])
        worker = threading.Thread(
            target=self._cross_platform_update_worker,
            args=(component,),
            name="tsun-diagnostic-update-check",
            daemon=True,
        )
        worker.start()

    def _cross_platform_update_worker(self, component: str) -> None:
        try:
            manifest = tsun_dump.fetch_update_manifest()
            gui_update = tsun_dump.select_update_component(
                manifest, component, APP_VERSION
            )
            dump_update = tsun_dump.select_update_component(
                manifest,
                tsun_dump.UPDATE_COMPONENT_DUMP,
                tsun_dump.TOOL_VERSION,
            )
            if gui_update is None and dump_update is not None:
                # Each packaged GUI embeds tsun_dump.py. If only the engine became
                # newer, a fresh package is still required for macOS/Linux.
                gui_update = tsun_dump.select_update_component(
                    manifest, component, "0.0.0"
                )
            if gui_update is None:
                self.events.put(("update_current",))
            else:
                self.events.put(("update_available_manual", gui_update["version"]))
        except Exception:
            self.events.put(("update_failed",))


def main() -> int:
    # Windows keeps the existing verified self-replacement helper. macOS/Linux
    # packages intentionally use manual package replacement for now.
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
