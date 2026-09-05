#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Small Windows GUI wrapper for the TSUN Local read-only hardware dump tool.

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
APP_VERSION = "1.0.1"
REPORT_EMAIL = getattr(tsun_dump, "REPORT_EMAIL", "dev@jptstar.com")

_TEXT = {
    "fr": {
        "title": "TSUN Local — Diagnostic",
        "intro": (
            "Outil portable Windows — aucune installation ni Python requis.\n"
            "Le diagnostic est strictement en lecture seule et anonymise les données sensibles.\n"
            f"Envoyez le rapport JSON généré à : {REPORT_EMAIL}"
        ),
        "timing": (
            "Lancez-le pendant que le problème est présent, avant de recharger l'intégration."
        ),
        "disabled": "J'ai désactivé l'entrée TSUN Local concernée dans Home Assistant",
        "host": "IP du logger (optionnel)",
        "sn": "Monitor SN (optionnel — non enregistré)",
        "folder": "Dossier de sortie",
        "browse": "Parcourir…",
        "run": "Lancer le diagnostic complet",
        "open": "Ouvrir le dossier",
        "ready": "Prêt.",
        "running": "Diagnostic en cours…",
        "done": f"Diagnostic terminé. Envoyez le fichier JSON généré à {REPORT_EMAIL}.",
        "failed": "Le diagnostic s'est terminé avec une erreur.",
        "need_disable": (
            "Désactivez d'abord l'entrée TSUN Local concernée dans Home Assistant, "
            "puis cochez la case de confirmation."
        ),
        "input_title": "Information nécessaire",
        "cancelled": "Diagnostic annulé.",
        "folder_error": "Impossible d'utiliser le dossier de sortie sélectionné.",
        "footer": "Moteur tsun_dump.py v{dump} · Interface v{gui} · Lecture seule",
    },
    "en": {
        "title": "TSUN Local — Diagnostic",
        "intro": (
            "Portable Windows tool — no installation or Python required.\n"
            "The diagnostic is strictly read-only and redacts sensitive data.\n"
            f"Send the generated JSON report to: {REPORT_EMAIL}"
        ),
        "timing": "Run it while the problem is present, before reloading the integration.",
        "disabled": "I disabled the affected TSUN Local entry in Home Assistant",
        "host": "Logger IP (optional)",
        "sn": "Monitor SN (optional — not stored)",
        "folder": "Output folder",
        "browse": "Browse…",
        "run": "Run full diagnostic",
        "open": "Open folder",
        "ready": "Ready.",
        "running": "Diagnostic running…",
        "done": f"Diagnostic complete. Send the generated JSON file to {REPORT_EMAIL}.",
        "failed": "The diagnostic ended with an error.",
        "need_disable": (
            "First disable the affected TSUN Local entry in Home Assistant, "
            "then tick the confirmation box."
        ),
        "input_title": "Information required",
        "cancelled": "Diagnostic cancelled.",
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

        self.root.title(self.t["title"])
        self.root.geometry("760x620")
        self.root.minsize(680, 540)

        self.confirm_disabled = tk.BooleanVar(value=False)
        self.host = tk.StringVar()
        self.monitor_sn = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(self._default_output_dir()))
        self.status = tk.StringVar(value=self.t["ready"])

        self._build_ui()
        self.root.after(100, self._poll_events)

    @staticmethod
    def _default_output_dir() -> Path:
        home = Path.home()
        for candidate in (home / "Desktop", home / "Documents", home):
            if candidate.exists():
                return candidate
        return home

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(8, weight=1)

        ttk.Label(outer, text=APP_NAME, font=("Segoe UI", 18, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(outer, text=self.t["intro"], wraplength=700).grid(
            row=1, column=0, sticky="w", pady=(6, 2)
        )
        ttk.Label(outer, text=self.t["timing"], wraplength=700).grid(
            row=2, column=0, sticky="w", pady=(0, 12)
        )

        ttk.Checkbutton(
            outer, text=self.t["disabled"], variable=self.confirm_disabled
        ).grid(row=3, column=0, sticky="w", pady=(0, 12))

        fields = ttk.Frame(outer)
        fields.grid(row=4, column=0, sticky="ew")
        fields.columnconfigure(1, weight=1)

        ttk.Label(fields, text=self.t["host"]).grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        ttk.Entry(fields, textvariable=self.host, width=30).grid(
            row=0, column=1, sticky="ew"
        )
        ttk.Label(fields, text=self.t["sn"]).grid(
            row=1, column=0, sticky="w", padx=(0, 10), pady=(8, 0)
        )
        ttk.Entry(fields, textvariable=self.monitor_sn, width=30).grid(
            row=1, column=1, sticky="ew", pady=(8, 0)
        )
        ttk.Label(fields, text=self.t["folder"]).grid(
            row=2, column=0, sticky="w", padx=(0, 10), pady=(8, 0)
        )
        ttk.Entry(fields, textvariable=self.output_dir).grid(
            row=2, column=1, sticky="ew", pady=(8, 0)
        )
        ttk.Button(fields, text=self.t["browse"], command=self._choose_folder).grid(
            row=2, column=2, padx=(8, 0), pady=(8, 0)
        )

        buttons = ttk.Frame(outer)
        buttons.grid(row=5, column=0, sticky="ew", pady=(14, 8))
        self.run_button = ttk.Button(buttons, text=self.t["run"], command=self._start)
        self.run_button.pack(side="left")
        ttk.Button(buttons, text=self.t["open"], command=self._open_folder).pack(
            side="left", padx=(8, 0)
        )

        ttk.Label(outer, textvariable=self.status, font=("Segoe UI", 10, "bold")).grid(
            row=6, column=0, sticky="w", pady=(0, 8)
        )

        log_frame = ttk.Frame(outer)
        log_frame.grid(row=8, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log = tk.Text(log_frame, height=16, wrap="word", state="disabled")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        footer = self.t["footer"].format(
            dump=getattr(tsun_dump, "TOOL_VERSION", "?"), gui=APP_VERSION
        )
        ttk.Label(outer, text=footer).grid(row=9, column=0, sticky="w", pady=(8, 0))

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
            messagebox.showwarning(APP_NAME, self.t["need_disable"])
            return

        folder = Path(self.output_dir.get()).expanduser()
        try:
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_NAME, f"{self.t['folder_error']}\n\n{exc}")
            return

        self.run_button.configure(state="disabled")
        self.status.set(self.t["running"])
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
                    self.status.set(str(event[1]))
                    self.run_button.configure(state="normal")
                    if bool(event[2]):
                        messagebox.showinfo(APP_NAME, str(event[1]))
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
