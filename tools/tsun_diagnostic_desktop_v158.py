#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""TSUN Local Diagnostic 1.5.8 UI/persistence refinements."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import tsun_diagnostic_desktop as legacy

APP_NAME = legacy.APP_NAME
APP_VERSION = "1.5.8"
MAX_DEVICE_ROWS = legacy.MAX_DEVICE_ROWS
PROFILE_DIR_NAME = "TSUN Local Diagnostic"
PROFILE_FILE_NAME = "upload_profile.json"

legacy.APP_VERSION = APP_VERSION
legacy.base.APP_VERSION = APP_VERSION
legacy.upload_app.APP_VERSION = APP_VERSION

legacy.upload_app._TEXT["fr"].update(
    {
        "devices_hint": (
            "Jusqu’à 10 types. Tapez une partie du modèle (ex. MS, MP3000, 800) "
            "pour filtrer la liste, puis choisissez la quantité."
        ),
        "saved_profile": (
            "Nom et micro-onduleurs mémorisés sur ce PC, y compris après mise à jour. "
            "Vous pouvez les modifier à tout moment."
        ),
        "model": "Modèle / recherche",
        "select_model": "Sélectionnez un modèle dans les propositions pour : {value}",
    }
)
legacy.upload_app._TEXT["en"].update(
    {
        "devices_hint": (
            "Up to 10 types. Type part of a model (e.g. MS, MP3000, 800) "
            "to filter the list, then choose the quantity."
        ),
        "saved_profile": (
            "Name and microinverters are saved on this PC, including across updates. "
            "You can change them at any time."
        ),
        "model": "Model / search",
        "select_model": "Select a model from the suggestions for: {value}",
    }
)


def _profile_candidates() -> list[Path]:
    """Stable user locations; independent of the portable EXE path/version."""
    paths: list[Path] = []
    for env_name in ("LOCALAPPDATA", "APPDATA"):
        value = os.environ.get(env_name)
        if value:
            candidate = Path(value) / PROFILE_DIR_NAME / PROFILE_FILE_NAME
            if candidate not in paths:
                paths.append(candidate)
    if not paths:
        root = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
        paths.append(root / PROFILE_DIR_NAME / PROFILE_FILE_NAME)
    return paths


def upload_profile_path() -> Path:
    return _profile_candidates()[0]


def _read_profile(path: Path) -> dict[str, object] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(raw, dict):
        return None

    name = raw.get("tester_name", "")
    if not isinstance(name, str):
        name = ""
    devices: list[dict[str, object]] = []
    source = raw.get("declared_devices", [])
    if isinstance(source, list):
        for item in source[:MAX_DEVICE_ROWS]:
            if not isinstance(item, dict):
                continue
            model = item.get("model")
            if model not in legacy.upload_app.TSUN_MICROINVERTER_MODELS:
                continue
            try:
                quantity = int(item.get("quantity", 1))
            except (TypeError, ValueError):
                continue
            if 1 <= quantity <= 99:
                devices.append({"model": str(model), "quantity": quantity})
    return {"tester_name": name[:80], "declared_devices": devices}


def _write_profile(path: Path, profile: dict[str, object]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
    except OSError:
        pass


def load_upload_profile(path: Path | None = None) -> dict[str, object]:
    if path is not None:
        return _read_profile(path) or {"tester_name": "", "declared_devices": []}

    fallback: dict[str, object] | None = None
    selected: dict[str, object] | None = None
    for candidate in _profile_candidates():
        profile = _read_profile(candidate)
        if profile is None:
            continue
        if profile.get("tester_name") or profile.get("declared_devices"):
            selected = profile
            break
        fallback = fallback or profile
    selected = selected or fallback or {"tester_name": "", "declared_devices": []}

    # Migrates the former APPDATA-only profile and keeps a second user-local copy.
    if selected.get("tester_name") or selected.get("declared_devices"):
        save_upload_profile(
            str(selected.get("tester_name", "")),
            list(selected.get("declared_devices", [])),
        )
    return selected


def save_upload_profile(
    tester_name: str,
    devices: list[dict[str, object]],
    path: Path | None = None,
) -> None:
    profile: dict[str, object] = {
        "schema_version": 1,
        "tester_name": tester_name.strip()[:80],
        "declared_devices": devices[:MAX_DEVICE_ROWS],
    }
    targets = [path] if path is not None else _profile_candidates()
    for target in targets:
        if target is not None:
            _write_profile(target, profile)


# The self-updater only replaces TSUN-Local-Diagnostic.exe. These profile
# locations therefore remain untouched. Monkey-patch the inherited upload path
# so all save/load calls use the durable storage immediately.
legacy.load_upload_profile = load_upload_profile
legacy.save_upload_profile = save_upload_profile


def filter_microinverter_models(query: str) -> tuple[str, ...]:
    """Return catalogue matches for any typed fragment, prefix matches first."""
    text = "".join(query.casefold().split())
    models = legacy.upload_app.TSUN_MICROINVERTER_MODELS
    if not text:
        return models

    ranked: list[tuple[int, str]] = []
    for model in models:
        full = "".join(model.casefold().split())
        short = full.removeprefix("tsol-")
        if text not in full and text not in short:
            continue
        rank = 0 if short.startswith(text) else (1 if full.startswith(text) else 2)
        ranked.append((rank, model))
    ranked.sort(key=lambda item: (item[0], item[1].casefold()))
    return tuple(model for _rank, model in ranked)


class CleanDiagnosticApp(legacy.CleanDiagnosticApp):
    """Editable filtered model rows, wheel-safe controls and durable autosave."""

    def __init__(self, root: tk.Tk) -> None:
        self._profile_save_job: str | None = None
        super().__init__(root)

    @staticmethod
    def _block_mousewheel(_event: tk.Event[tk.Misc]) -> str:
        return "break"

    def _bind_no_wheel_change(self, widget: tk.Misc) -> None:
        widget.bind("<MouseWheel>", self._block_mousewheel)
        widget.bind("<Button-4>", self._block_mousewheel)
        widget.bind("<Button-5>", self._block_mousewheel)

    def _post_filtered_values(self, combo: ttk.Combobox) -> None:
        try:
            combo.tk.call("ttk::combobox::Post", str(combo))
        except tk.TclError:
            pass

    def _on_model_typing(
        self,
        event: tk.Event[ttk.Combobox],
        model_var: tk.StringVar,
        combo: ttk.Combobox,
        spin: tk.Spinbox,
    ) -> None:
        if event.keysym in {
            "Up", "Down", "Left", "Right", "Prior", "Next", "Home", "End",
            "Tab", "Return", "Escape",
        }:
            return
        query = model_var.get().strip()
        matches = filter_microinverter_models(query)
        try:
            combo.configure(values=matches)
            self._compact_quantity_state(model_var, spin)
            old_job = getattr(combo, "_tsun_filter_job", None)
            if old_job is not None:
                try:
                    combo.after_cancel(old_job)
                except tk.TclError:
                    pass
            combo._tsun_filter_job = (
                combo.after(180, lambda widget=combo: self._post_filtered_values(widget))
                if query and matches
                else None
            )
        except tk.TclError:
            pass
        self._queue_profile_save()

    def _normalize_model(
        self, model_var: tk.StringVar, combo: ttk.Combobox, spin: tk.Spinbox
    ) -> None:
        typed = model_var.get().strip()
        if typed:
            exact = next(
                (m for m in legacy.upload_app.TSUN_MICROINVERTER_MODELS if m.casefold() == typed.casefold()),
                None,
            )
            if exact is None:
                matches = filter_microinverter_models(typed)
                if len(matches) == 1:
                    exact = matches[0]
            if exact is not None:
                model_var.set(exact)
        try:
            combo.configure(values=filter_microinverter_models(model_var.get()))
        except tk.TclError:
            pass
        self._compact_quantity_state(model_var, spin)
        self._queue_profile_save()

    def _build_compact_device_rows(self, parent: tk.Frame) -> None:
        self._compact_device_rows = []
        shell = tk.Frame(parent, bg=legacy.base._SOFT_BLUE, highlightthickness=1, highlightbackground=legacy.base._LINE)
        shell.pack(fill="x")
        shell.columnconfigure(1, weight=1)

        tk.Label(shell, text="#", bg=legacy.base._SOFT_BLUE, fg=legacy.base._MUTED,
                 font=("Segoe UI", 8, "bold"), width=3).grid(row=0, column=0, padx=(8, 4), pady=(6, 3))
        tk.Label(shell, text=self.u["model"], bg=legacy.base._SOFT_BLUE, fg=legacy.base._MUTED,
                 font=("Segoe UI", 8, "bold"), anchor="w").grid(row=0, column=1, sticky="ew", padx=4, pady=(6, 3))
        tk.Label(shell, text=self.u["quantity"], bg=legacy.base._SOFT_BLUE, fg=legacy.base._MUTED,
                 font=("Segoe UI", 8, "bold")).grid(row=0, column=2, padx=(4, 10), pady=(6, 3))

        saved_devices = self._saved_upload_profile.get("declared_devices", [])
        if not isinstance(saved_devices, list):
            saved_devices = []

        for index in range(MAX_DEVICE_ROWS):
            saved = saved_devices[index] if index < len(saved_devices) else {}
            model_value = saved.get("model", "") if isinstance(saved, dict) else ""
            quantity_value = saved.get("quantity", 1) if isinstance(saved, dict) else 1
            model_var = tk.StringVar(value=str(model_value))
            quantity_var = tk.StringVar(value=str(quantity_value))

            combo = ttk.Combobox(
                shell,
                textvariable=model_var,
                values=filter_microinverter_models(str(model_value)),
                state="normal",
                font=("Segoe UI", 9),
                height=18,
            )
            spin = tk.Spinbox(
                shell, from_=1, to=99, width=5, textvariable=quantity_var,
                justify="center", relief="solid", bd=1, font=("Segoe UI", 9),
                state="normal" if model_var.get().strip() else "disabled",
            )
            tk.Label(shell, text=str(index + 1), bg=legacy.base._SOFT_BLUE, fg=legacy.base._MUTED,
                     font=("Segoe UI", 8)).grid(row=index + 1, column=0, padx=(8, 4), pady=2)
            combo.grid(row=index + 1, column=1, sticky="ew", padx=4, pady=2, ipady=2)
            spin.grid(row=index + 1, column=2, padx=(4, 10), pady=2, ipady=2)

            self._bind_no_wheel_change(combo)
            self._bind_no_wheel_change(spin)
            combo.bind(
                "<KeyRelease>",
                lambda event, var=model_var, widget=combo, qty=spin: self._on_model_typing(event, var, widget, qty),
            )
            combo.bind(
                "<<ComboboxSelected>>",
                lambda _event, var=model_var, widget=combo, qty=spin: self._normalize_model(var, widget, qty),
            )
            combo.bind(
                "<FocusOut>",
                lambda _event, var=model_var, widget=combo, qty=spin: self._normalize_model(var, widget, qty),
            )
            quantity_var.trace_add("write", lambda *_args: self._queue_profile_save())
            self._compact_device_rows.append((model_var, quantity_var, combo, spin))

        tk.Frame(shell, bg=legacy.base._SOFT_BLUE, height=5).grid(row=MAX_DEVICE_ROWS + 1, column=0, columnspan=3)

    def _profile_devices(self, *, strict: bool) -> list[dict[str, object]]:
        merged: dict[str, dict[str, object]] = {}
        for model_var, quantity_var, _combo, _spin in self._compact_device_rows:
            typed = model_var.get().strip()
            if not typed:
                continue
            exact = next(
                (m for m in legacy.upload_app.TSUN_MICROINVERTER_MODELS if m.casefold() == typed.casefold()),
                None,
            )
            if exact is None:
                matches = filter_microinverter_models(typed)
                if len(matches) == 1:
                    exact = matches[0]
                    model_var.set(exact)
                elif strict:
                    raise legacy.report_upload.ReportUploadError(self.u["select_model"].format(value=typed))
                else:
                    continue
            try:
                quantity = int(quantity_var.get().strip())
            except ValueError as exc:
                if strict:
                    raise legacy.report_upload.ReportUploadError(f"quantity must be an integer for {exact}") from exc
                continue
            if not 1 <= quantity <= 99:
                if strict:
                    raise legacy.report_upload.ReportUploadError(f"quantity must be between 1 and 99 for {exact}")
                continue
            key = exact.casefold()
            if key in merged:
                total = int(merged[key]["quantity"]) + quantity
                if total > 99:
                    if strict:
                        raise legacy.report_upload.ReportUploadError(f"device quantity exceeds 99 for {exact}")
                    continue
                merged[key]["quantity"] = total
            else:
                merged[key] = {"model": exact, "quantity": quantity}
        return list(merged.values())

    def _collect_declared_devices(self) -> list[dict[str, object]]:
        return self._profile_devices(strict=True)

    def _queue_profile_save(self) -> None:
        if self.upload_window is None:
            return
        if self._profile_save_job is not None:
            try:
                self.root.after_cancel(self._profile_save_job)
            except tk.TclError:
                pass
        try:
            self._profile_save_job = self.root.after(300, self._persist_profile)
        except tk.TclError:
            self._profile_save_job = None

    def _persist_profile(self) -> None:
        self._profile_save_job = None
        tester = ""
        try:
            tester = self._dialog["tester"].get()
        except (KeyError, tk.TclError):
            pass
        devices = self._profile_devices(strict=False)
        save_upload_profile(tester, devices)
        self._saved_upload_profile = {"tester_name": tester.strip(), "declared_devices": devices}

    def _show_upload_dialog(self) -> None:
        super()._show_upload_dialog()
        if self.upload_window is None:
            return
        try:
            self._dialog["tester"].bind("<KeyRelease>", lambda _event: self._queue_profile_save(), add="+")
        except (KeyError, tk.TclError):
            pass

    def _close_upload_window(self) -> None:
        if self.upload_thread and self.upload_thread.is_alive():
            super()._close_upload_window()
            return
        if self._profile_save_job is not None:
            try:
                self.root.after_cancel(self._profile_save_job)
            except tk.TclError:
                pass
            self._profile_save_job = None
        if self.upload_window is not None:
            self._persist_profile()
        super()._close_upload_window()

    def _set_dialog_inputs_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        try:
            self._dialog["tester"].configure(state=state)
            self._dialog["consent"].configure(state=state)
        except (KeyError, tk.TclError):
            pass
        for model_var, _quantity_var, combo, spin in self._compact_device_rows:
            try:
                combo.configure(state="normal" if enabled else "disabled")
                spin.configure(state="normal" if enabled and model_var.get().strip() else "disabled")
            except tk.TclError:
                pass
        try:
            allow_send = enabled and self._dialog["consent_var"].get()
            self._dialog["send"].configure(state="normal" if allow_send else "disabled")
        except (KeyError, tk.TclError):
            pass


def main() -> int:
    internal_result = legacy.base._internal_update_mode()
    if internal_result is not None:
        return internal_result
    root = tk.Tk()
    CleanDiagnosticApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
