#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Stable cross-platform entry point for TSUN Local Diagnostic.

The same Tk interface is packaged for Windows, macOS and Linux. Platform-specific
code here is intentionally limited to profile storage, opening folders and
selecting the correct rolling-release update component. The read-only diagnostic
engine and report-upload flow remain shared with the existing desktop modules.
"""

from __future__ import annotations

import os
from pathlib import Path
import platform
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox

import tsun_dump
import tsun_diagnostic_desktop_v159 as ui

# Keep the public compatibility shape used by existing tests and helper code:
# `previous` remains the 1.5.8 UI/persistence layer while `ui` is the 1.5.10
# report-link layer inherited by the final application class below.
previous = ui.previous

APP_NAME = ui.APP_NAME
APP_VERSION = "1.5.11"
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
    root = tk.Tk()
    CleanDiagnosticApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
