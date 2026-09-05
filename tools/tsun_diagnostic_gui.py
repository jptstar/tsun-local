#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Compact desktop GUI wrapper for the TSUN Local read-only hardware dump tool.

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
APP_VERSION = "1.3.0"
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
            "Désactivez l'entrée TSUN Local concernée dans Home Assistant pour éviter "
            "deux interrogations simultanées du logger."
        ),
        "disabled": "TSUN Local est désactivé",
        "auto_title": "2 · Lancez le diagnostic",
        "auto_text": (
            "Tout est automatique : logger, protocole et appareils sont recherchés "
            "sans réglage dans la majorité des cas."
        ),
        "run": "Lancer le diagnostic",
        "ready": "Prêt à analyser",
        "running": "Diagnostic en cours…",
        "done": f"Diagnostic terminé — envoyez le JSON à {REPORT_EMAIL}",
        "failed": "Le diagnostic s'est terminé avec une erreur.",
        "cancelled": "Diagnostic annulé.",
        "output_title": "3 · Envoyez le rapport",
        "output": "Dossier du JSON",
        "change": "Modifier",
        "open": "Ouvrir le dossier",
        "send": "Adresse d'envoi",
        "copy": "Copier l'adresse",
        "copied": "Adresse copiée",
        "report_hint": "Le JSON est anonymisé. Vous pouvez le vérifier avant l'envoi.",
        "advanced_show": "Options avancées",
        "details_show": "Détails techniques",
        "advanced_title": "Options avancées",
        "details_title": "Détails techniques",
        "host": "IP du logger",
        "host_hint": "Optionnel — vide = détection automatique",
        "sn": "Monitor SN",
        "sn_hint": "Optionnel — utilisé pour communiquer, jamais enregistré dans le JSON",
        "folder": "Dossier de sortie",
        "browse": "Parcourir…",
        "close": "Fermer",
        "input_title": "Information nécessaire",
        "folder_error": "Impossible d'utiliser le dossier de sortie sélectionné.",
        "footer": "Moteur tsun_dump.py v{dump} · Interface v{gui} · Lecture seule",
    },
    "en": {
        "title": "TSUN Local Diagnostic",
        "subtitle": "Portable local hardware diagnostic with a strictly read-only engine.",
        "readonly": "READ-ONLY",
        "step_title": "1 · Disable TSUN Local",
        "step_text": (
            "Disable the affected TSUN Local entry in Home Assistant to avoid two "
            "simultaneous polling sessions on the logger."
        ),
        "disabled": "TSUN Local is disabled",
        "auto_title": "2 · Run the diagnostic",
        "auto_text": (
            "Automatic by default: logger, protocol and devices are discovered "
            "without extra settings in most cases."
        ),
        "run": "Run diagnostic",
        "ready": "Ready to scan",
        "running": "Diagnostic running…",
        "done": f"Diagnostic complete — send the JSON to {REPORT_EMAIL}",
        "failed": "The diagnostic ended with an error.",
        "cancelled": "Diagnostic cancelled.",
        "output_title": "3 · Send the report",
        "output": "JSON folder",
        "change": "Change",
        "open": "Open folder",
        "send": "Send to",
        "copy": "Copy address",
        "copied": "Address copied",
        "report_hint": "The JSON is anonymized. You can review it before sending.",
        "advanced_show": "Advanced options",
        "details_show": "Technical details",
        "advanced_title": "Advanced options",
        "details_title": "Technical details",
        "host": "Logger IP",
        "host_hint": "Optional — empty = automatic discovery",
        "sn": "Monitor SN",
        "sn_hint": "Optional — used for communication, never stored in the JSON",
        "folder": "Output folder",
        "browse": "Browse…",
        "close": "Close",
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
        self.advanced_window: tk.Toplevel | None = None
        self.details_window: tk.Toplevel | None = None
        self.log: tk.Text | None = None
        self.log_buffer: list[str] = []

        self.root.title(self.t["title"])
        self.root.geometry("920x570")
        self.root.minsize(860, 540)
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
            font=("Segoe UI", 9 if compact else 11, "bold"),
            padx=12 if compact else 18,
            pady=6 if compact else 11,
            highlightthickness=1 if not primary else 0,
            highlightbackground=_LINE,
        )

    def _section_title(self, parent: tk.Misc, text: str) -> None:
        tk.Label(
            parent,
            text=text,
            bg=_CARD,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x")

    def _build_ui(self) -> None:
        content = tk.Frame(self.root, bg=_BG)
        content.pack(fill="both", expand=True, padx=24, pady=18)

        header = tk.Frame(content, bg=_BG)
        header.pack(fill="x", pady=(0, 14))
        title_row = tk.Frame(header, bg=_BG)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text=self.t["title"],
            bg=_BG,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 21, "bold"),
        ).pack(side="left")
        tk.Label(
            title_row,
            text=self.t["readonly"],
            bg=_SOFT_GREEN,
            fg=_SUCCESS,
            font=("Segoe UI", 9, "bold"),
            padx=9,
            pady=4,
        ).pack(side="right", pady=(3, 0))
        tk.Label(
            header,
            text=self.t["subtitle"],
            bg=_BG,
            fg=_MUTED,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

        main = tk.Frame(content, bg=_BG)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1, uniform="main")
        main.columnconfigure(1, weight=1, uniform="main")
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        right = tk.Frame(main, bg=_BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(7, 0))

        step1 = self._card(left)
        step1.pack(fill="x", pady=(0, 12))
        step1_inner = tk.Frame(step1, bg=_CARD)
        step1_inner.pack(fill="x", padx=18, pady=15)
        self._section_title(step1_inner, self.t["step_title"])
        tk.Label(
            step1_inner,
            text=self.t["step_text"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=385,
            anchor="w",
        ).pack(fill="x", pady=(5, 10))
        self.confirm_check = tk.Checkbutton(
            step1_inner,
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

        step2 = self._card(left)
        step2.pack(fill="both", expand=True)
        step2_inner = tk.Frame(step2, bg=_CARD)
        step2_inner.pack(fill="both", expand=True, padx=18, pady=15)
        self._section_title(step2_inner, self.t["auto_title"])
        tk.Label(
            step2_inner,
            text=self.t["auto_text"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=385,
            anchor="w",
        ).pack(fill="x", pady=(5, 14))

        self.run_button = self._flat_button(
            step2_inner, self.t["run"], self._start, primary=True
        )
        self.run_button.pack(fill="x")
        self.run_button.configure(state="disabled")

        self.progress = ttk.Progressbar(step2_inner, mode="indeterminate")
        self.progress.pack(fill="x", pady=(10, 0))
        self.status_label = tk.Label(
            step2_inner,
            textvariable=self.status,
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 9, "bold"),
            justify="left",
            wraplength=385,
            anchor="w",
        )
        self.status_label.pack(fill="x", pady=(10, 0))

        step3 = self._card(right)
        step3.pack(fill="both", expand=True)
        step3_inner = tk.Frame(step3, bg=_CARD)
        step3_inner.pack(fill="both", expand=True, padx=18, pady=15)
        self._section_title(step3_inner, self.t["output_title"])

        tk.Label(
            step3_inner,
            text=self.t["send"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x", pady=(14, 0))
        tk.Label(
            step3_inner,
            text=REPORT_EMAIL,
            bg=_CARD,
            fg=_ACCENT,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(2, 8))
        self.copy_button = self._flat_button(
            step3_inner, self.t["copy"], self._copy_email, compact=True
        )
        self.copy_button.pack(anchor="w")

        divider = tk.Frame(step3_inner, bg=_LINE, height=1)
        divider.pack(fill="x", pady=15)

        tk.Label(
            step3_inner,
            text=self.t["output"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 8),
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            step3_inner,
            textvariable=self.output_dir,
            bg=_SOFT_BLUE,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 9),
            justify="left",
            wraplength=385,
            anchor="w",
            padx=9,
            pady=8,
        ).pack(fill="x", pady=(4, 9))

        folder_buttons = tk.Frame(step3_inner, bg=_CARD)
        folder_buttons.pack(fill="x")
        self._flat_button(
            folder_buttons, self.t["open"], self._open_folder, compact=True
        ).pack(side="left")
        self._flat_button(
            folder_buttons, self.t["change"], self._choose_folder, compact=True
        ).pack(side="left", padx=(8, 0))

        tk.Label(
            step3_inner,
            text=self.t["report_hint"],
            bg=_CARD,
            fg=_MUTED,
            font=("Segoe UI", 8),
            justify="left",
            wraplength=385,
            anchor="w",
        ).pack(fill="x", pady=(15, 0))

        bottom = tk.Frame(content, bg=_BG)
        bottom.pack(fill="x", pady=(12, 0))
        self.advanced_button = self._flat_button(
            bottom, self.t["advanced_show"], self._show_advanced, compact=True
        )
        self.advanced_button.pack(side="left")
        self.details_button = self._flat_button(
            bottom, self.t["details_show"], self._show_details, compact=True
        )
        self.details_button.pack(side="left", padx=(8, 0))

        footer = self.t["footer"].format(
            dump=getattr(tsun_dump, "TOOL_VERSION", "?"), gui=APP_VERSION
        )
        tk.Label(
            bottom,
            text=footer,
            bg=_BG,
            fg=_MUTED,
            font=("Segoe UI", 8),
            anchor="e",
        ).pack(side="right", pady=6)

    def _popup_field(
        self,
        parent: tk.Misc,
        label: str,
        hint: str,
        variable: tk.StringVar,
    ) -> None:
        holder = tk.Frame(parent, bg=_CARD)
        holder.pack(fill="x", pady=(0, 13))
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

    def _show_advanced(self) -> None:
        if self.advanced_window and self.advanced_window.winfo_exists():
            self.advanced_window.deiconify()
            self.advanced_window.lift()
            self.advanced_window.focus_force()
            return

        win = tk.Toplevel(self.root)
        self.advanced_window = win
        win.title(self.t["advanced_title"])
        win.geometry("590x355")
        win.minsize(540, 330)
        win.configure(bg=_BG)
        win.transient(self.root)

        def close() -> None:
            self.advanced_window = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", close)
        card = self._card(win)
        card.pack(fill="both", expand=True, padx=18, pady=18)
        inner = tk.Frame(card, bg=_CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        self._section_title(inner, self.t["advanced_title"])
        fields = tk.Frame(inner, bg=_CARD)
        fields.pack(fill="x", pady=(14, 0))
        self._popup_field(fields, self.t["host"], self.t["host_hint"], self.host)
        self._popup_field(fields, self.t["sn"], self.t["sn_hint"], self.monitor_sn)

        tk.Label(
            fields,
            text=self.t["folder"],
            bg=_CARD,
            fg=_TEXT_COLOR,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        ).pack(fill="x")
        folder_row = tk.Frame(fields, bg=_CARD)
        folder_row.pack(fill="x", pady=(5, 0))
        tk.Entry(
            folder_row,
            textvariable=self.output_dir,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Segoe UI", 9),
        ).pack(side="left", fill="x", expand=True, ipady=6)
        self._flat_button(
            folder_row, self.t["browse"], self._choose_folder, compact=True
        ).pack(side="right", padx=(8, 0))
        self._flat_button(inner, self.t["close"], close, compact=True).pack(
            anchor="e", pady=(14, 0)
        )

    def _show_details(self) -> None:
        if self.details_window and self.details_window.winfo_exists():
            self.details_window.deiconify()
            self.details_window.lift()
            self.details_window.focus_force()
            return

        win = tk.Toplevel(self.root)
        self.details_window = win
        win.title(self.t["details_title"])
        win.geometry("780x440")
        win.minsize(620, 340)
        win.configure(bg=_BG)
        win.transient(self.root)

        def close() -> None:
            self.log = None
            self.details_window = None
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", close)
        card = self._card(win)
        card.pack(fill="both", expand=True, padx=16, pady=16)
        inner = tk.Frame(card, bg=_CARD)
        inner.pack(fill="both", expand=True, padx=12, pady=12)

        log = tk.Text(
            inner,
            wrap="word",
            state="normal",
            bg="#0e2036",
            fg="#dceaff",
            insertbackground="#ffffff",
            relief="flat",
            bd=0,
            font=("Consolas", 9),
            padx=10,
            pady=10,
        )
        scroll = ttk.Scrollbar(inner, orient="vertical", command=log.yview)
        log.configure(yscrollcommand=scroll.set)
        log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        log.insert("end", "".join(self.log_buffer))
        log.see("end")
        log.configure(state="disabled")
        self.log = log

    def _sync_run_button(self, *_args: Any) -> None:
        if self.worker and self.worker.is_alive():
            self.run_button.configure(state="disabled")
            return
        state = "normal" if self.confirm_disabled.get() else "disabled"
        self.run_button.configure(state=state)

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
        self.log_buffer.append(text)
        if self.log is not None and self.log.winfo_exists():
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
                    if not success:
                        self._show_details()
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
