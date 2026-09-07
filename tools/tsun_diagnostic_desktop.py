#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Clean four-step TSUN Local Diagnostic desktop layout."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

import tsun_diagnostic_app as upload_app
import tsun_diagnostic_gui as base
import tsun_report_upload as report_upload

APP_NAME = base.APP_NAME
APP_VERSION = "1.5.7"
PROJECT_URL = "https://github.com/jptstar/tsun-local"
COPYRIGHT_TEXT = "© 2026 @jptstar · GitHub"

MAGIC_TEST_HOST = "89:89:89:89"
MAGIC_TEST_SN = "89898989"
MAX_DEVICE_ROWS = 10

base.APP_VERSION = APP_VERSION
upload_app.APP_VERSION = APP_VERSION

base._TEXT["fr"].update(
    {
        "done": "Diagnostic terminé — vous pouvez maintenant envoyer le rapport.",
        "output_title": "4 · Envoi manuel par e-mail",
        "send": "Adresse e-mail",
        "report_hint": "Optionnel — à utiliser uniquement en cas de problème avec l’envoi direct.",
        "update_current": "✓ Application à jour",
    }
)
base._TEXT["en"].update(
    {
        "done": "Diagnostic complete — you can now send the report.",
        "output_title": "4 · Manual report by e-mail",
        "send": "E-mail address",
        "report_hint": "Optional — use only if there is a problem with direct upload.",
        "update_current": "✓ Application is up to date",
    }
)

upload_app._TEXT["fr"].update(
    {
        "title": "3 · Envoi direct du rapport",
        "summary": (
            "Méthode recommandée. Envoyez le JSON anonymisé directement à TSUN Local. "
            "Rien n’est transmis sans votre accord."
        ),
        "button": "Envoyer le rapport",
        "test_running": "Mode test hors site — création d’un rapport de test…",
        "test_ready": "Mode test hors site — rapport de test prêt à être envoyé.",
        "published": "Rapport publié — ouvrez ce lien pour voir exactement ce qui a été envoyé :",
        "open_published": "Voir le rapport publié",
        "devices": "Micro-onduleurs TSUN installés (optionnel)",
        "devices_hint": "Ajoutez jusqu’à 10 types. Choisissez le modèle puis la quantité.",
        "saved_profile": "Nom et micro-onduleurs mémorisés sur ce PC. Vous pouvez les modifier à tout moment.",
        "model": "Modèle",
        "quantity": "Qté",
        "link_waiting": "Le lien de consultation apparaîtra ici après l’envoi.",
        "link_missing": "Rapport envoyé, mais le serveur n’a pas retourné de lien de consultation.",
    }
)
upload_app._TEXT["en"].update(
    {
        "title": "3 · Direct report upload",
        "summary": (
            "Recommended method. Send the anonymized JSON directly to TSUN Local. "
            "Nothing is transmitted without your consent."
        ),
        "button": "Send report",
        "test_running": "Off-site test mode — creating a test report…",
        "test_ready": "Off-site test mode — test report ready to upload.",
        "published": "Report published — open this link to see exactly what was sent:",
        "open_published": "View published report",
        "devices": "Installed TSUN microinverters (optional)",
        "devices_hint": "Add up to 10 types. Choose the model and then the quantity.",
        "saved_profile": "Name and microinverters are saved on this PC. You can change them at any time.",
        "model": "Model",
        "quantity": "Qty",
        "link_waiting": "The viewing link will appear here after upload.",
        "link_missing": "Report uploaded, but the server did not return a viewing link.",
    }
)


def upload_profile_path() -> Path:
    """Persistent, user-local profile. Never stores consent or diagnostic data."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        root = Path(appdata)
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        root = Path(xdg) if xdg else Path.home() / ".config"
    return root / "TSUN Local Diagnostic" / "upload_profile.json"


def load_upload_profile(path: Path | None = None) -> dict[str, object]:
    target = path or upload_profile_path()
    try:
        raw = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"tester_name": "", "declared_devices": []}
    if not isinstance(raw, dict):
        return {"tester_name": "", "declared_devices": []}

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
            if model not in upload_app.TSUN_MICROINVERTER_MODELS:
                continue
            try:
                quantity = int(item.get("quantity", 1))
            except (TypeError, ValueError):
                continue
            if 1 <= quantity <= 99:
                devices.append({"model": str(model), "quantity": quantity})
    return {"tester_name": name[:80], "declared_devices": devices}


def save_upload_profile(
    tester_name: str,
    devices: list[dict[str, object]],
    path: Path | None = None,
) -> None:
    """Save only the optional tester profile; consent is intentionally never saved."""
    target = path or upload_profile_path()
    payload = {
        "tester_name": tester_name.strip()[:80],
        "declared_devices": devices[:MAX_DEVICE_ROWS],
    }
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
    except OSError:
        pass


class CleanDiagnosticApp(upload_app.UploadDiagnosticApp):
    """Present the diagnostic as four visually ordered steps."""

    def __init__(self, root: tk.Tk) -> None:
        self._view_link_host: tk.Frame | None = None
        self._view_link_url = ""
        self._view_link_label: tk.Label | None = None
        self._compact_device_rows: list[
            tuple[tk.StringVar, tk.StringVar, ttk.Combobox, tk.Spinbox]
        ] = []
        self._saved_upload_profile = load_upload_profile()
        super().__init__(root)
        self.root.geometry("980x700")
        self.root.minsize(920, 650)
        self.host.trace_add("write", self._sync_run_button)
        self.monitor_sn.trace_add("write", self._sync_run_button)
        self.root.after(150, self._sync_view_link)

    def _build_ui(self) -> None:
        base.DiagnosticApp._build_ui(self)

        content = self.root.winfo_children()[0]
        content_children = content.winfo_children()
        if len(content_children) < 3:
            raise RuntimeError("unexpected diagnostic UI structure")

        main = content_children[1]
        bottom_toolbar = content_children[2]
        columns = main.winfo_children()
        if len(columns) < 2:
            raise RuntimeError("unexpected diagnostic column structure")
        right = columns[1]

        for widget in right.winfo_children():
            widget.destroy()

        self._build_direct_step(right)
        self._build_manual_step(content, bottom_toolbar)
        self._build_project_footer(bottom_toolbar)

    def _build_project_footer(self, bottom_toolbar: tk.Frame) -> None:
        link = tk.Label(
            bottom_toolbar,
            text=COPYRIGHT_TEXT,
            bg=base._BG,
            fg=base._ACCENT,
            font=("Segoe UI", 8, "underline"),
            cursor="hand2",
            anchor="e",
        )
        link.pack(side="right", padx=(12, 0), pady=6)
        link.bind("<Button-1>", lambda _event: webbrowser.open(PROJECT_URL))

    def _build_direct_step(self, right: tk.Frame) -> None:
        direct_card = self._card(right)
        direct_card.pack(fill="both", expand=True)
        direct_inner = tk.Frame(direct_card, bg=base._CARD)
        direct_inner.pack(fill="both", expand=True, padx=18, pady=15)

        heading = tk.Frame(direct_inner, bg=base._CARD)
        heading.pack(fill="x")
        tk.Label(
            heading,
            text=self.u["title"],
            bg=base._CARD,
            fg=base._TEXT_COLOR,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(side="left")
        tk.Label(
            heading,
            text="RECOMMANDÉ" if self.lang == "fr" else "RECOMMENDED",
            bg=base._SOFT_GREEN,
            fg=base._SUCCESS,
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=3,
        ).pack(side="right")

        tk.Label(
            direct_inner,
            text=self.u["summary"],
            bg=base._CARD,
            fg=base._MUTED,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=400,
            anchor="w",
        ).pack(fill="x", pady=(8, 18))

        privacy_box = tk.Frame(direct_inner, bg=base._SOFT_BLUE)
        privacy_box.pack(fill="x", pady=(0, 18))
        tk.Label(
            privacy_box,
            text=(
                "✓ Diagnostic anonymisé  •  ✓ Consentement explicite  •  ✓ HTTPS"
                if self.lang == "fr"
                else "✓ Anonymized diagnostic  •  ✓ Explicit consent  •  ✓ HTTPS"
            ),
            bg=base._SOFT_BLUE,
            fg=base._TEXT_COLOR,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
            padx=10,
            pady=9,
        ).pack(fill="x")

        self.upload_status = tk.StringVar(value=self.u["waiting"])
        self.upload_status_label = tk.Label(
            direct_inner,
            textvariable=self.upload_status,
            bg=base._CARD,
            fg=base._MUTED,
            font=("Segoe UI", 9, "bold"),
            justify="left",
            wraplength=400,
            anchor="w",
        )
        self.upload_status_label.pack(fill="x", pady=(0, 10))

        self.upload_button = self._flat_button(
            direct_inner,
            self.u["button"],
            self._show_upload_dialog,
            primary=True,
        )
        self.upload_button.pack(fill="x")
        self.upload_button.configure(state="disabled")

    def _build_manual_step(self, content: tk.Frame, bottom_toolbar: tk.Frame) -> None:
        manual_card = self._card(content)
        manual_card.pack(fill="x", pady=(12, 0), before=bottom_toolbar)
        inner = tk.Frame(manual_card, bg=base._CARD)
        inner.pack(fill="x", padx=18, pady=13)
        inner.columnconfigure(0, weight=2)
        inner.columnconfigure(1, weight=2)
        inner.columnconfigure(2, weight=3)

        title_block = tk.Frame(inner, bg=base._CARD)
        title_block.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        title_row = tk.Frame(title_block, bg=base._CARD)
        title_row.pack(fill="x")
        tk.Label(
            title_row,
            text=self.t["output_title"],
            bg=base._CARD,
            fg=base._TEXT_COLOR,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        ).pack(side="left")
        tk.Label(
            title_row,
            text=(
                "OPTIONNEL · EN CAS DE PROBLÈME"
                if self.lang == "fr"
                else "OPTIONAL · IF NEEDED"
            ),
            bg=base._SOFT_BLUE,
            fg=base._MUTED,
            font=("Segoe UI", 8, "bold"),
            padx=7,
            pady=3,
        ).pack(side="left", padx=(8, 0))
        tk.Label(
            title_block,
            text=self.t["report_hint"],
            bg=base._CARD,
            fg=base._MUTED,
            font=("Segoe UI", 8),
            justify="left",
            wraplength=275,
            anchor="w",
        ).pack(fill="x", pady=(6, 0))

        email_block = tk.Frame(inner, bg=base._CARD)
        email_block.grid(row=0, column=1, sticky="nsew", padx=(0, 18))
        tk.Label(
            email_block,
            text=self.t["send"],
            bg=base._CARD,
            fg=base._MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            email_block,
            text=base.REPORT_EMAIL,
            bg=base._CARD,
            fg=base._ACCENT,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(2, 7))
        self.copy_button = self._flat_button(
            email_block, self.t["copy"], self._copy_email, compact=True
        )
        self.copy_button.pack(anchor="w")

        file_block = tk.Frame(inner, bg=base._CARD)
        file_block.grid(row=0, column=2, sticky="nsew")
        tk.Label(
            file_block,
            text=self.t["output"],
            bg=base._CARD,
            fg=base._MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            file_block,
            textvariable=self.output_dir,
            bg=base._SOFT_BLUE,
            fg=base._TEXT_COLOR,
            font=("Segoe UI", 8),
            justify="left",
            wraplength=320,
            anchor="w",
            padx=8,
            pady=6,
        ).pack(fill="x", pady=(3, 7))
        buttons = tk.Frame(file_block, bg=base._CARD)
        buttons.pack(fill="x")
        self._flat_button(
            buttons, self.t["open"], self._open_folder, compact=True
        ).pack(side="left")
        self._flat_button(
            buttons, self.t["change"], self._choose_folder, compact=True
        ).pack(side="left", padx=(8, 0))

    def _is_magic_test_mode(self) -> bool:
        return (
            self.host.get().strip() == MAGIC_TEST_HOST
            and self.monitor_sn.get().strip() == MAGIC_TEST_SN
        )

    def _sync_run_button(self, *_args: object) -> None:
        if not hasattr(self, "run_button"):
            return
        if self.update_busy or (self.worker and self.worker.is_alive()):
            self.run_button.configure(state="disabled")
            return
        enabled = self.confirm_disabled.get() or self._is_magic_test_mode()
        self.run_button.configure(state="normal" if enabled else "disabled")

    def _start(self) -> None:
        if not self._is_magic_test_mode():
            super()._start()
            return
        if self.worker and self.worker.is_alive():
            return

        folder = Path(self.output_dir.get()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"{self.t['folder_error']}\n\n{exc}")
            return

        self.latest_reports = []
        self.uploaded_reports.clear()
        self.run_button.configure(state="disabled")
        self.confirm_check.configure(state="disabled")
        self.status.set(self.u["test_running"])
        self.status_label.configure(fg=base._ACCENT)
        self.upload_status.set(self.u["capturing"])
        self.upload_status_label.configure(fg=base._ACCENT)
        self.progress.start(12)
        self._append_log("\n=== TSUN Local Diagnostic — OFF-SITE TEST MODE ===\n")
        self.worker = threading.Thread(
            target=self._run_dump,
            args=(folder, MAGIC_TEST_HOST, MAGIC_TEST_SN),
            daemon=True,
        )
        self.worker.start()

    def _run_dump(self, folder: Path, host: str, monitor_sn: str) -> None:
        if host != MAGIC_TEST_HOST or monitor_sn != MAGIC_TEST_SN:
            super()._run_dump(folder, host, monitor_sn)
            return

        now = datetime.now(timezone.utc)
        diagnostic = {
            "report_type": "test",
            "test_mode": True,
            "test_profile": "offsite_magic_trigger",
            "generated_at": now.isoformat(),
            "application": "TSUN Local Diagnostic",
            "application_version": APP_VERSION,
            "communication_attempted": False,
            "note": (
                "Synthetic off-site test report. No logger or microinverter was contacted; "
                "tester and declared-device fields can be exercised through the normal upload dialog."
            ),
        }
        path = folder / f"tsun_local_test_report_{now.strftime('%Y%m%d_%H%M%S')}.json"
        try:
            path.write_text(
                json.dumps(diagnostic, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            self.events.put(("log", f"Test report write failed: {exc}\n"))
            self.events.put(("status", self.t["failed"], False))
            return

        resolved = path.resolve()
        self.latest_reports = [resolved]
        self.uploaded_reports.discard(resolved)
        self.events.put(("log", f"Test report created: {path.name}\n"))
        self.events.put(("status", self.u["test_ready"], True))

    def _compact_quantity_state(
        self, model_var: tk.StringVar, spin: tk.Spinbox
    ) -> None:
        try:
            spin.configure(state="normal" if model_var.get().strip() else "disabled")
        except tk.TclError:
            pass

    def _build_compact_device_rows(self, parent: tk.Frame) -> None:
        self._compact_device_rows = []
        shell = tk.Frame(
            parent,
            bg=base._SOFT_BLUE,
            highlightthickness=1,
            highlightbackground=base._LINE,
        )
        shell.pack(fill="x")

        shell.columnconfigure(1, weight=1)
        tk.Label(
            shell,
            text="#",
            bg=base._SOFT_BLUE,
            fg=base._MUTED,
            font=("Segoe UI", 8, "bold"),
            width=3,
        ).grid(row=0, column=0, padx=(8, 4), pady=(6, 3))
        tk.Label(
            shell,
            text=self.u["model"],
            bg=base._SOFT_BLUE,
            fg=base._MUTED,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=4, pady=(6, 3))
        tk.Label(
            shell,
            text=self.u["quantity"],
            bg=base._SOFT_BLUE,
            fg=base._MUTED,
            font=("Segoe UI", 8, "bold"),
        ).grid(row=0, column=2, padx=(4, 10), pady=(6, 3))

        saved_devices = self._saved_upload_profile.get("declared_devices", [])
        if not isinstance(saved_devices, list):
            saved_devices = []
        choices = ("",) + upload_app.TSUN_MICROINVERTER_MODELS

        for index in range(MAX_DEVICE_ROWS):
            saved = saved_devices[index] if index < len(saved_devices) else {}
            model_value = saved.get("model", "") if isinstance(saved, dict) else ""
            quantity_value = saved.get("quantity", 1) if isinstance(saved, dict) else 1

            model_var = tk.StringVar(value=str(model_value))
            quantity_var = tk.StringVar(value=str(quantity_value))
            combo = ttk.Combobox(
                shell,
                textvariable=model_var,
                values=choices,
                state="readonly",
                font=("Segoe UI", 9),
                height=18,
            )
            spin = tk.Spinbox(
                shell,
                from_=1,
                to=99,
                width=5,
                textvariable=quantity_var,
                justify="center",
                relief="solid",
                bd=1,
                font=("Segoe UI", 9),
                state="normal" if model_var.get().strip() else "disabled",
            )
            tk.Label(
                shell,
                text=str(index + 1),
                bg=base._SOFT_BLUE,
                fg=base._MUTED,
                font=("Segoe UI", 8),
            ).grid(row=index + 1, column=0, padx=(8, 4), pady=2)
            combo.grid(
                row=index + 1,
                column=1,
                sticky="ew",
                padx=4,
                pady=2,
                ipady=2,
            )
            spin.grid(row=index + 1, column=2, padx=(4, 10), pady=2, ipady=2)
            combo.bind(
                "<<ComboboxSelected>>",
                lambda _event, var=model_var, widget=spin: self._compact_quantity_state(
                    var, widget
                ),
            )
            self._compact_device_rows.append((model_var, quantity_var, combo, spin))

        tk.Frame(shell, bg=base._SOFT_BLUE, height=5).grid(
            row=MAX_DEVICE_ROWS + 1, column=0, columnspan=3
        )

    def _collect_declared_devices(self) -> list[dict[str, object]]:
        merged: dict[str, dict[str, object]] = {}
        for model_var, quantity_var, _combo, _spin in self._compact_device_rows:
            model = model_var.get().strip()
            if not model:
                continue
            if model not in upload_app.TSUN_MICROINVERTER_MODELS:
                raise report_upload.ReportUploadError(
                    f"unknown TSUN microinverter model: {model}"
                )
            try:
                quantity = int(quantity_var.get().strip())
            except ValueError as exc:
                raise report_upload.ReportUploadError(
                    f"quantity must be an integer for {model}"
                ) from exc
            if not 1 <= quantity <= 99:
                raise report_upload.ReportUploadError(
                    f"quantity must be between 1 and 99 for {model}"
                )
            key = model.casefold()
            if key in merged:
                total = int(merged[key]["quantity"]) + quantity
                if total > 99:
                    raise report_upload.ReportUploadError(
                        f"device quantity exceeds 99 for {model}"
                    )
                merged[key]["quantity"] = total
            else:
                merged[key] = {"model": model, "quantity": quantity}
        return list(merged.values())

    def _set_dialog_inputs_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        try:
            self._dialog["tester"].configure(state=state)
            self._dialog["consent"].configure(state=state)
        except (KeyError, tk.TclError):
            pass

        for model_var, _quantity_var, combo, spin in self._compact_device_rows:
            try:
                combo.configure(state="readonly" if enabled else "disabled")
                spin.configure(
                    state="normal"
                    if enabled and model_var.get().strip()
                    else "disabled"
                )
            except tk.TclError:
                pass

        try:
            allow_send = enabled and self._dialog["consent_var"].get()
            self._dialog["send"].configure(
                state="normal" if allow_send else "disabled"
            )
        except (KeyError, tk.TclError):
            pass

    def _close_upload_window(self) -> None:
        self._compact_device_rows = []
        self._view_link_host = None
        self._view_link_url = ""
        self._view_link_label = None
        super()._close_upload_window()

    def _show_upload_dialog(self) -> None:
        paths = self._remaining()
        if not paths:
            messagebox.showinfo(APP_NAME, self.u["none"], parent=self.root)
            return
        if self.upload_window is not None:
            try:
                if self.upload_window.winfo_exists():
                    self.upload_window.lift()
                    self.upload_window.focus_force()
                    return
            except tk.TclError:
                pass

        self._saved_upload_profile = load_upload_profile()

        win = tk.Toplevel(self.root)
        self.upload_window = win
        win.title(self.u["dialog"])
        win.geometry("700x720")
        win.minsize(650, 680)
        win.configure(bg=base._BG)
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", self._close_upload_window)

        card = self._card(win)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        inner = tk.Frame(card, bg=base._CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=16)

        self._label(inner, self.u["dialog"], 15, True).pack(fill="x")
        self._label(
            inner, self.u["privacy"], 8, False, muted=True, wrap=620
        ).pack(fill="x", pady=(5, 8))

        file_text = " • ".join(p.name for p in paths)
        self._label(inner, file_text, 8, False, wrap=620, bg=base._SOFT_BLUE, padx=9, pady=6).pack(
            fill="x", pady=(0, 9)
        )

        self._label(inner, self.u["tester"], 9, True).pack(fill="x")
        tester = tk.StringVar(
            value=str(self._saved_upload_profile.get("tester_name", ""))
        )
        tester_entry = tk.Entry(
            inner,
            textvariable=tester,
            relief="solid",
            bd=1,
            font=("Segoe UI", 9),
        )
        tester_entry.pack(fill="x", ipady=5, pady=(3, 2))
        self._label(
            inner, self.u["saved_profile"], 8, False, muted=True, wrap=620
        ).pack(fill="x", pady=(0, 7))

        self._label(inner, self.u["devices"], 9, True).pack(fill="x")
        self._label(
            inner, self.u["devices_hint"], 8, False, muted=True
        ).pack(fill="x", pady=(1, 4))
        self._build_compact_device_rows(inner)

        consent = tk.BooleanVar(value=False)
        consent_box = tk.Checkbutton(
            inner,
            text=self.u["consent"],
            variable=consent,
            bg=base._CARD,
            fg=base._TEXT_COLOR,
            activebackground=base._CARD,
            activeforeground=base._TEXT_COLOR,
            selectcolor=base._CARD,
            font=("Segoe UI", 8, "bold"),
            justify="left",
            wraplength=620,
            anchor="w",
        )
        consent_box.pack(fill="x", pady=(9, 5))

        status = tk.StringVar(value="")
        status_label = self._label(inner, "", 8, True, muted=True, wrap=620)
        status_label.configure(textvariable=status)
        status_label.pack(fill="x")

        self._view_link_host = tk.Frame(inner, bg=base._SOFT_GREEN)
        self._view_link_host.pack(fill="x", pady=(7, 0))
        self._view_link_host.pack_forget()

        buttons = tk.Frame(inner, bg=base._CARD)
        buttons.pack(fill="x", pady=(9, 0))
        send = self._flat_button(
            buttons,
            self.u["send"],
            lambda: self._begin_upload(paths, tester.get(), consent.get()),
            primary=True,
            compact=True,
        )
        send.pack(side="left")
        send.configure(state="disabled")
        cancel = self._flat_button(
            buttons, self.u["cancel"], self._close_upload_window, compact=True
        )
        cancel.pack(side="right")
        consent.trace_add(
            "write",
            lambda *_: send.configure(
                state="normal" if consent.get() else "disabled"
            ),
        )
        self._dialog = {
            "status": status,
            "label": status_label,
            "send": send,
            "cancel": cancel,
            "tester": tester_entry,
            "consent": consent_box,
            "consent_var": consent,
        }

        win.update_idletasks()
        x = self.root.winfo_rootx() + max(
            0, (self.root.winfo_width() - win.winfo_width()) // 2
        )
        y = self.root.winfo_rooty() + max(
            0, (self.root.winfo_height() - win.winfo_height()) // 2
        )
        win.geometry(f"+{x}+{y}")
        win.lift()
        win.focus_force()

    def _begin_upload(
        self, paths: list[Path], tester_name: str, consent: bool
    ) -> None:
        if self.upload_thread and self.upload_thread.is_alive():
            return
        try:
            parsed = self._collect_declared_devices()
            report_upload.build_payload(
                {},
                consent=consent,
                tester_name=tester_name,
                declared_devices=parsed,
            )
        except report_upload.ReportUploadError as exc:
            messagebox.showerror(
                self.u["invalid"],
                str(exc),
                parent=self.upload_window or self.root,
            )
            return

        save_upload_profile(tester_name, parsed)
        self._saved_upload_profile = {
            "tester_name": tester_name.strip(),
            "declared_devices": parsed,
        }

        pending = [
            p
            for p in paths
            if p not in self.uploaded_reports and p.exists()
        ]
        if not pending:
            return

        self._set_dialog_inputs_enabled(False)
        self._dialog["label"].configure(fg=base._ACCENT)
        self._receipts = []
        self._view_link_url = ""
        if self._view_link_host is not None:
            try:
                self._view_link_host.pack_forget()
            except tk.TclError:
                pass
        self.upload_thread = threading.Thread(
            target=self._upload_reports,
            args=(pending, tester_name.strip(), parsed),
            daemon=True,
        )
        self.upload_thread.start()

    def _sync_view_link(self) -> None:
        try:
            if not self._receipts or self._view_link_host is None:
                return
            candidate = self._receipts[-1].get("view_url")
            url = (
                candidate
                if isinstance(candidate, str)
                and candidate.startswith("https://")
                else ""
            )

            if url and url != self._view_link_url:
                self._view_link_url = url
                for child in self._view_link_host.winfo_children():
                    child.destroy()
                tk.Label(
                    self._view_link_host,
                    text=self.u["published"],
                    bg=base._SOFT_GREEN,
                    fg=base._SUCCESS,
                    font=("Segoe UI", 8, "bold"),
                    anchor="w",
                    padx=10,
                    pady=5,
                ).pack(fill="x")
                self._view_link_label = tk.Label(
                    self._view_link_host,
                    text=url,
                    bg=base._SOFT_GREEN,
                    fg=base._ACCENT,
                    font=("Segoe UI", 8, "underline"),
                    cursor="hand2",
                    justify="left",
                    wraplength=610,
                    anchor="w",
                    padx=10,
                    pady=2,
                )
                self._view_link_label.pack(fill="x")
                self._view_link_label.bind(
                    "<Button-1>",
                    lambda _event, link=url: webbrowser.open(link),
                )
                self._flat_button(
                    self._view_link_host,
                    self.u["open_published"],
                    lambda link=url: webbrowser.open(link),
                    compact=True,
                ).pack(anchor="w", padx=10, pady=(4, 8))
                self._view_link_host.pack(fill="x", pady=(7, 0))
            elif not url and not self._view_link_url:
                for child in self._view_link_host.winfo_children():
                    child.destroy()
                tk.Label(
                    self._view_link_host,
                    text=self.u["link_missing"],
                    bg=base._SOFT_GREEN,
                    fg=base._MUTED,
                    font=("Segoe UI", 8, "bold"),
                    anchor="w",
                    padx=10,
                    pady=7,
                ).pack(fill="x")
                self._view_link_host.pack(fill="x", pady=(7, 0))
        except tk.TclError:
            pass
        finally:
            try:
                self.root.after(200, self._sync_view_link)
            except tk.TclError:
                pass


def main() -> int:
    internal_result = base._internal_update_mode()
    if internal_result is not None:
        return internal_result

    root = tk.Tk()
    CleanDiagnosticApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
