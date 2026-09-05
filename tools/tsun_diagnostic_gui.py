#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Small desktop GUI wrapper for the TSUN Local read-only hardware dump tool.

The executable built from this file contains the existing ``tsun_dump.py``
engine. It does not implement any additional TSUN write command: all device
communication remains delegated to the privacy-safe, strictly read-only dump
engine.
"""

from __future__ import annotations

import builtins
import io
import locale
import os
from pathlib import Path
import queue
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Any

import tsun_dump

APP_NAME = "TSUN Local Diagnostic"
APP_VERSION = "1.2.0"
REPORT_EMAIL = getattr(tsun_dump, "REPORT_EMAIL", "dev@jptstar.com")

_BG = "#f4f7fb"
_CARD = "#ffffff"
_TEXT_COLOR = "#10223a"
_MUTED = "#617188"
_LINE = "#dce5ef"
_ACCENT = "#1167d8"
_ACCENT_HOVER = "#0d57b8"
_SUCCESS = "#148660"
_DANGER = "#b42318"
_SOFT_BLUE = "#eaf2ff"
_SOFT_GREEN = "#e7f7f1"

_TEXT = {
    "fr": {
        "title": "Diagnostic TSUN Local",
        "subtitle": "Diagnostic matériel local, portable et strictement en lecture seule.",
        "readonly": "LECTURE SEULE",
        "step_title": "1 · Désactivez TSUN Local",
        "step_text": (
            "Désactivez uniquement l'entrée TSUN Local concernée dans Home Assistant. "
            "Cela évite que Home Assistant et l'outil interrogent le logger en même temps."
        ),
        "disabled": "TSUN Local est désactivé dans Home Assistant",
        "auto_title": "Tout est automatique",
        "auto_text": (
            "Laissez les options avancées vides dans la majorité des cas : le logger, "
            "le protocole et les appareils sont recherchés automatiquement."
        ),
        "run": "2 · Lancer le diagnostic",
        "ready": "Prêt à analyser",
        "running": "Diagnostic en cours…",
        "done": f"Diagnostic terminé — envoyez le JSON à {REPORT_EMAIL}",
        "failed": "Le diagnostic s'est terminé avec une erreur. Ouvrez les détails pour en savoir plus.",
        "cancelled": "Diagnostic annulé.",
        "output_title": "3 · Rapport à envoyer",
        "output": "Enregistrement dans",
        "change": "Modifier",
        "open": "Ouvrir le dossier",
        "send": "Envoyer le JSON à",
        "copy": "Copier l'adresse",
        "copied": "Adresse copiée",
        "advanced_show": "Options avancées",
        "advanced_hide": "Masquer les options avancées",
        "details_show": "Afficher les détails techniques",
        "details_hide": "Masquer les détails techniques",
        "host": "IP du logger",
        "host_hint": "Optionnel — laissez vide pour la détection automatique",
        "sn": "Monitor SN",
        "sn_hint": "Optionnel — utilisé pour la communication, jamais enregistré dans le JSON",
        "folder": "Dossier de sortie",
        "browse": "Parcourir…",
        "input_title": "Information nécessaire",
        "folder_error": "Impossible d'utiliser le dossier de sortie sélectionné.",
        "footer": "Moteur tsun_dump.py v{dump} · Interface v{gui} · Lecture seule",
    },
    "en": {
        "title": "TSUN Local Diagnostic",
        "subtitle": "Portable, local hardware diagnostic with a strictly read-only engine.",
        "readonly": "READ-ONLY",
        "step_title": "1 · Disable TSUN Local",
        "step_text": (
            "Disable only the affected TSUN Local entry in Home Assistant. "
            "This prevents Home Assistant and the diagnostic tool from polling the logger at the same time."
        ),
        "disabled": "TSUN Local is disabled in Home Assistant",
        "auto_title": "Automatic by default",
        "auto_text": (
            "Leave advanced options empty in most cases: the logger, protocol and devices "
            "are discovered automatically."
        ),
        "run": "2 · Run diagnostic",
        "ready": "Ready to scan",
        "running": "Diagnostic running…",
        "done": f"Diagnostic complete — send the JSON to {REPORT_EMAIL}",
        "failed": "The diagnostic ended with an error. Open technical details for more information.",
        "cancelled": "Diagnostic cancelled.",
        "output_title": "3 · Report to send",
        "output": "Saved to",
        "change": "Change",
        "open": "Open folder",
        "send": "Send the JSON to",
        "copy": "Copy address",
        "copied": "Address copied",
        "advanced_show": "Advanced options",
        "advanced_hide": "Hide advanced options",
        "details_show": "Show technical details",
        "details_hide": "Hide technical details",
        "host": "Logger IP",
        "host_hint": "Optional — leave empty for automatic discovery",
        "sn": "Monitor SN",
        "sn_hint": "Optional — used for communication, never stored in the JSON",
        "folder": "Output folder",
        "browse": "Browse…",
        "input_title": "Information required",
        "folder_error": "The selected output folder cannot be used.",
        "footer": "tsun_dump.py engine v{dump} · GUI v{gui} · Read-only",
    },
}


def _language() -> str:
    try:
        current = (locale.getlocale()[0] or "").lower()
    except (ValueError, TypeError):
        current = ""
    return "fr" if current.startswith("fr") else "en"


class _QueueWriter(io.TextIOBase):
    def __init__(self, events: queue.Queue[tuple[Any, ...]]) -> None:
        self._events = events

    def write(self, text: str) -> int:
        if text:
            self._events.put(("log", text))
        return len(text)

    def flush(self) -> None:
        return None


class DiagnosticApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lang = _language()
        self.t = _TEXT[self.lang]
        self.events: queue.Queue[tuple[Any, ...]] = queue.Queue()
        self.worker: threading.Thread | None = None
        self.advanced_visible = False
        self.details_visible = False

        self.root.title(self.t["title"])
        self.root.geometry("780x690")
        self.root.minsize(700, 600)
        self.root.configure(bg=_BG)

        self.confirm_disabled = tk.BooleanVar(value=False)
        self.host = tk.StringVar()
        self.monitor_sn = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(self._default_output_dir()))
        self.status = tk.StringVar(value=self.t["ready"])

        self._configure_ttk()
        self._build_ui()
        self.confirm_disabled.trace_add("write", self._sync_run_button)
        self.root.after(100, self._poll_events)

    @staticmethod
    def _default_output_dir() -> Path:
        home = Path.home()
        for candidate in (home / "Desktop", home / "Documents", home):
            if candidate.exists():
                return candidate
        return home

    def _configure_ttk(self) -> None:
        style = ttk.Style(self.root)
        style.configure("TProgressbar", thickness=6)

    @staticmethod
    def _card(parent: tk.Misc) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=_CARD,
            highlightbackground=_LINE,
            highlightcolor=_LINE,
            highlightthickness=1,
            bd=0,
        )

    @staticmethod
    def _flat_button(
        parent: tk.Misc,
        text: str,
        command: Any,
        *,
        primary: bool = False,
        compact: bool = False,
    ) -> tk.Button:
        bg = _ACCENT if primary else _CARD
        fg = "#ffffff" if primary else _TEXT_COLOR
        active_bg = _ACCENT_HOVER if primary else _SOFT_BLUE
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            disabledforeground="#96a1b0",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10 if compact else 11, "bold"),
            padx=13 if compact else 20,
            pady=7 if compact else 12,
            highlightthickness=1 if not primary else 0,
            highlightbackground=_LINE,
        )

    def _build_ui(self) -> None:
        canvas = tk.Canvas(self.root, bg=_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        outer = tk.Frame(canvas, bg=_BG)
        window = canvas.create_window((0, 0), window=outer, anchor="nw")

        def _resize_canvas(event: tk.Event[Any]) -> None:
            canvas.itemconfigure(window, width=event.width)

        def _resize_scroll_region(_event: tk.Event[Any]) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", _resize_canvas)
        outer.bind("<Configure>", _resize_scroll_region)

        content = tk.Frame(outer, bg=_BG)
        content.pack(fill="both", expand=True, padx=28, pady=24)

        header = tk.Frame(content, bg=_BG)
        header.pack(fill="x", pady=(0, 18))
        title_row = tk.Frame(header, bg=_BG)
        title_row.pack(fill="x")
        tk.Label(
            title_row,
            text=self.t["title"],
            bg=_BG,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 22, "bold"),
        ).pack(side="left")
        tk.Label(
            title_row,
            text=self.t["readonly"],
            bg=_SOFT_GREEN,
            fg=_SUCCESS,
            font=("Segoe UI", 9, "bold"),
            padx=9,
            pady=4,
        ).pack(side="right", pady=(4, 0))
        tk.Label(
            header,
            text=self.t["subtitle"],
            bg=_BG,
            fg=_MUTED,
            font=("Segoe UI", 10),
            anchor="w",
        ).pack(fill="x", pady=(5, 0))

        start_card = self._card(content)
        start_card.pack(fill="x", pady=(0, 14))
        start_inner = tk.Frame(start_card, bg=_CARD)
        start_inner.pack(fill="x", padx=20, pady=18)
        tk.Label(
            start_inner,
            text=self.t["step_title"],
            bg=_CARD,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            start_inner,
            text=self.t["step_text"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=680,
            anchor="w",
        ).pack(fill="x", pady=(5, 12))
        self.confirm_check = tk.Checkbutton(
            start_inner,
            text=self.t["disabled"],
            variable=self.confirm_disabled,
            bg=_CARD,
            fg=_TEXT_COLOR,
            activebackground=_CARD,
            activeforeground=_TEXT_COLOR,
            selectcolor=_CARD,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            padx=0,
            pady=0,
        )
        self.confirm_check.pack(fill="x")

        auto_card = self._card(content)
        auto_card.pack(fill="x", pady=(0, 14))
        auto_inner = tk.Frame(auto_card, bg=_CARD)
        auto_inner.pack(fill="x", padx=20, pady=17)
        tk.Label(
            auto_inner,
            text=self.t["auto_title"],
            bg=_CARD,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            auto_inner,
            text=self.t["auto_text"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=680,
            anchor="w",
        ).pack(fill="x", pady=(5, 0))

        action_area = tk.Frame(content, bg=_BG)
        action_area.pack(fill="x", pady=(2, 14))
        self.run_button = self._flat_button(
            action_area, self.t["run"], self._start, primary=True
        )
        self.run_button.pack(fill="x")
        self.run_button.configure(state="disabled")
        self.progress = ttk.Progressbar(action_area, mode="indeterminate")
        self.progress.pack(fill="x", pady=(8, 0))
        self.status_label = tk.Label(
            action_area,
            textvariable=self.status,
            bg=_BG,
            fg=_MUTED,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(8, 0))

        report_card = self._card(content)
        report_card.pack(fill="x", pady=(0, 14))
        report_inner = tk.Frame(report_card, bg=_CARD)
        report_inner.pack(fill="x", padx=20, pady=17)
        tk.Label(
            report_inner,
            text=self.t["output_title"],
            bg=_CARD,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x")

        folder_row = tk.Frame(report_inner, bg=_CARD)
        folder_row.pack(fill="x", pady=(10, 0))
        folder_text = tk.Frame(folder_row, bg=_CARD)
        folder_text.pack(side="left", fill="x", expand=True)
        tk.Label(
            folder_text,
            text=self.t["output"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            folder_text,
            textvariable=self.output_dir,
            bg=_CARD,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x", pady=(1, 0))
        self._flat_button(
            folder_row, self.t["change"], self._choose_folder, compact=True
        ).pack(side="right", padx=(10, 0))

        email_row = tk.Frame(report_inner, bg=_CARD)
        email_row.pack(fill="x", pady=(14, 0))
        email_text = tk.Frame(email_row, bg=_CARD)
        email_text.pack(side="left", fill="x", expand=True)
        tk.Label(
            email_text,
            text=self.t["send"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            email_text,
            text=REPORT_EMAIL,
            bg=_CARD,
            fg=_ACCENT,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(1, 0))
        self.copy_button = self._flat_button(
            email_row, self.t["copy"], self._copy_email, compact=True
        )
        self.copy_button.pack(side="right", padx=(10, 0))

        button_row = tk.Frame(report_inner, bg=_CARD)
        button_row.pack(fill="x", pady=(14, 0))
        self._flat_button(
            button_row, self.t["open"], self._open_folder, compact=True
        ).pack(side="left")

        self.advanced_button = self._flat_button(
            content,
            self.t["advanced_show"],
            self._toggle_advanced,
            compact=True,
        )
        self.advanced_button.pack(anchor="w", pady=(0, 8))

        self.advanced_card = self._card(content)
        advanced_inner = tk.Frame(self.advanced_card, bg=_CARD)
        advanced_inner.pack(fill="x", padx=20, pady=17)

        self._field(
            advanced_inner,
            self.t["host"],
            self.t["host_hint"],
            self.host,
            row=0,
        )
        self._field(
            advanced_inner,
            self.t["sn"],
            self.t["sn_hint"],
            self.monitor_sn,
            row=1,
        )
        advanced_inner.columnconfigure(0, weight=1)

        folder_adv = tk.Frame(advanced_inner, bg=_CARD)
        folder_adv.grid(row=2, column=0, sticky="ew", pady=(11, 0))
        tk.Label(
            folder_adv,
            text=self.t["folder"],
            bg=_CARD,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x")
        folder_entry_row = tk.Frame(folder_adv, bg=_CARD)
        folder_entry_row.pack(fill="x", pady=(5, 0))
        tk.Entry(
            folder_entry_row,
            textvariable=self.output_dir,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Segoe UI", 9),
        ).pack(side="left", fill="x", expand=True, ipady=6)
        self._flat_button(
            folder_entry_row, self.t["browse"], self._choose_folder, compact=True
        ).pack(side="right", padx=(8, 0))

        self.details_button = self._flat_button(
            content,
            self.t["details_show"],
            self._toggle_details,
            compact=True,
        )
        self.details_button.pack(anchor="w", pady=(0, 8))

        self.log_card = self._card(content)
        log_inner = tk.Frame(self.log_card, bg=_CARD)
        log_inner.pack(fill="both", expand=True, padx=12, pady=12)
        self.log = tk.Text(
            log_inner,
            height=12,
            wrap="word",
            state="disabled",
            bg="#0e2036",
            fg="#dceaff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            font=("Consolas", 9),
            padx=10,
            pady=10,
        )
        scroll = ttk.Scrollbar(log_inner, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        footer = self.t["footer"].format(
            dump=getattr(tsun_dump, "TOOL_VERSION", "?"), gui=APP_VERSION
        )
        tk.Label(
            content,
            text=footer,
            bg=_BG,
            fg=_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", pady=(8, 6))

    def _field(
        self,
        parent: tk.Misc,
        label: str,
        hint: str,
        variable: tk.StringVar,
        *,
        row: int,
    ) -> None:
        holder = tk.Frame(parent, bg=_CARD)
        holder.grid(row=row, column=0, sticky="ew", pady=(0 if row == 0 else 11, 0))
        tk.Label(
            holder,
            text=label,
            bg=_CARD,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            holder,
            text=hint,
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", pady=(1, 4))
        tk.Entry(
            holder,
            textvariable=variable,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Segoe UI", 9),
        ).pack(fill="x", ipady=6)

    def _sync_run_button(self, *_args: Any) -> None:
        if self.worker and self.worker.is_alive():
            self.run_button.configure(state="disabled")
            return
        state = "normal" if self.confirm_disabled.get() else "disabled"
        self.run_button.configure(state=state)

    def _toggle_advanced(self) -> None:
        self.advanced_visible = not self.advanced_visible
        if self.advanced_visible:
            self.advanced_card.pack(fill="x", pady=(0, 14), before=self.details_button)
            self.advanced_button.configure(text=self.t["advanced_hide"])
        else:
            self.advanced_card.pack_forget()
            self.advanced_button.configure(text=self.t["advanced_show"])

    def _toggle_details(self) -> None:
        self.details_visible = not self.details_visible
        if self.details_visible:
            self.log_card.pack(fill="both", expand=True, pady=(0, 14), after=self.details_button)
            self.details_button.configure(text=self.t["details_hide"])
        else:
            self.log_card.pack_forget()
            self.details_button.configure(text=self.t["details_show"])

    def _copy_email(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(REPORT_EMAIL)
        original = self.t["copy"]
        self.copy_button.configure(text=self.t["copied"])
        self.root.after(1500, lambda: self.copy_button.configure(text=original))

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(initialdir=self.output_dir.get() or None)
        if selected:
            self.output_dir.set(selected)

    def _open_folder(self) -> None:
        folder = Path(self.output_dir.get()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(folder))  # type: ignore[attr-defined]
            else:
                messagebox.showinfo(APP_NAME, str(folder))
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"{self.t['folder_error']}\n\n{exc}")

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.confirm_disabled.get():
            return

        folder = Path(self.output_dir.get()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"{self.t['folder_error']}\n\n{exc}")
            return

        self.run_button.configure(state="disabled")
        self.confirm_check.configure(state="disabled")
        self.status.set(self.t["running"])
        self.status_label.configure(fg=_ACCENT)
        self.progress.start(12)
        self._append_log("\n=== TSUN Local Diagnostic ===\n")

        host = self.host.get().strip()
        monitor_sn = self.monitor_sn.get().strip()
        self.worker = threading.Thread(
            target=self._run_dump,
            args=(folder, host, monitor_sn),
            daemon=True,
        )
        self.worker.start()

    def _request_input(self, prompt: str = "") -> str:
        done = threading.Event()
        result: dict[str, str | None] = {"value": None}
        self.events.put(("input", prompt, done, result))
        done.wait()
        value = result["value"]
        if value is None:
            raise EOFError("User cancelled interactive input")
        return value

    def _run_dump(self, folder: Path, host: str, monitor_sn: str) -> None:
        previous_argv = sys.argv[:]
        previous_cwd = Path.cwd()
        previous_stdout = sys.stdout
        previous_stderr = sys.stderr
        previous_input = builtins.input
        writer = _QueueWriter(self.events)

        args = ["tsun_dump.py", "--full"]
        if host:
            args.extend(["--host", host])
        if monitor_sn:
            args.extend(["--monitor-sn", monitor_sn])

        exit_code = 1
        cancelled = False
        try:
            os.chdir(folder)
            sys.argv = args
            sys.stdout = writer
            sys.stderr = writer
            builtins.input = self._request_input
            result = tsun_dump.main()
            exit_code = int(result or 0)
        except EOFError:
            cancelled = True
            self.events.put(("status", self.t["cancelled"], False))
        except SystemExit as exc:
            exit_code = int(exc.code or 0) if isinstance(exc.code, int) else 1
        except Exception as exc:  # GUI boundary for non-technical users.
            self.events.put(("log", f"\n{type(exc).__name__}: {exc}\n"))
            exit_code = 1
        finally:
            builtins.input = previous_input
            sys.stdout = previous_stdout
            sys.stderr = previous_stderr
            sys.argv = previous_argv
            os.chdir(previous_cwd)
            if not cancelled and exit_code == 0:
                self.events.put(("status", self.t["done"], True))
            elif not cancelled:
                self.events.put(("status", self.t["failed"], False))

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "log":
                    self._append_log(str(event[1]))
                elif kind == "status":
                    success = bool(event[2])
                    self.status.set(str(event[1]))
                    self.progress.stop()
                    self.confirm_check.configure(state="normal")
                    self.status_label.configure(fg=_SUCCESS if success else _DANGER)
                    self._sync_run_button()
                    if not success and not self.details_visible:
                        self._toggle_details()
                elif kind == "input":
                    prompt, done, result = str(event[1]), event[2], event[3]
                    value = simpledialog.askstring(
                        self.t["input_title"], prompt, parent=self.root
                    )
                    result["value"] = value
                    done.set()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._poll_events)


def main() -> int:
    root = tk.Tk()
    DiagnosticApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
