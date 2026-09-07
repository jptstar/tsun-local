#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""TSUN Local Diagnostic GUI with optional explicit-consent report upload."""

from __future__ import annotations

from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from typing import Any

import tsun_diagnostic_gui as base
import tsun_report_upload as report_upload

APP_NAME = base.APP_NAME
APP_VERSION = "1.5.0"
base.APP_VERSION = APP_VERSION

_TEXT = {
    "fr": {
        "title": "Envoi direct du rapport",
        "summary": "Après le diagnostic, envoyez le JSON anonymisé directement à TSUN Local. L’envoi reste facultatif.",
        "waiting": "Disponible après un diagnostic réussi.",
        "capturing": "Diagnostic en cours…",
        "ready": "{count} rapport(s) prêt(s).",
        "sent": "Rapport(s) envoyé(s).",
        "button": "Envoyer le rapport",
        "dialog": "Envoyer le rapport TSUN Local",
        "privacy": "Le JSON anonymisé sera envoyé par HTTPS puis stocké dans un dépôt privé. Aucun jeton GitHub ni clé privée n’est intégré à l’application.",
        "files": "Rapport(s) à envoyer",
        "tester": "Nom ou pseudonyme (optionnel)",
        "tester_hint": "Laissez vide pour un envoi anonyme.",
        "devices": "Micro-onduleurs installés (optionnel)",
        "devices_hint": "Un modèle par ligne, par ex. TSOL-MX500 x2 ou 2x TSOL-MX500.",
        "consent": "J’accepte l’envoi de ce diagnostic anonymisé à TSUN Local pour l’analyse de compatibilité et de communication.",
        "send": "Envoyer maintenant",
        "cancel": "Annuler",
        "progress": "Envoi {current}/{total}…",
        "complete": "Envoi terminé. ID : {ids}",
        "error": "Envoi interrompu : {error}",
        "none": "Aucun nouveau rapport. Lancez d’abord un diagnostic.",
        "invalid": "Données d’envoi invalides",
        "busy": "Un envoi est en cours. Attendez sa fin avant de fermer.",
    },
    "en": {
        "title": "Direct report upload",
        "summary": "After the diagnostic, send the anonymized JSON directly to TSUN Local. Upload remains optional.",
        "waiting": "Available after a successful diagnostic.",
        "capturing": "Diagnostic running…",
        "ready": "{count} report(s) ready.",
        "sent": "Report(s) uploaded.",
        "button": "Send report",
        "dialog": "Send TSUN Local report",
        "privacy": "The anonymized JSON is sent over HTTPS then stored in a private repository. No GitHub token or private key is embedded in the app.",
        "files": "Report(s) to send",
        "tester": "Name or nickname (optional)",
        "tester_hint": "Leave empty for an anonymous upload.",
        "devices": "Installed microinverters (optional)",
        "devices_hint": "One model per line, e.g. TSOL-MX500 x2 or 2x TSOL-MX500.",
        "consent": "I agree to send this anonymized diagnostic to TSUN Local for compatibility and communication analysis.",
        "send": "Send now",
        "cancel": "Cancel",
        "progress": "Uploading {current}/{total}…",
        "complete": "Upload complete. ID: {ids}",
        "error": "Upload stopped: {error}",
        "none": "No new report. Run a diagnostic first.",
        "invalid": "Invalid upload data",
        "busy": "An upload is running. Wait for it to finish before closing.",
    },
}

# Keep the old e-mail route only as a fallback; direct upload is the normal path.
base._TEXT["fr"].update({
    "done": "Diagnostic terminé — le rapport peut maintenant être envoyé directement.",
    "output_title": "3 · Rapport local",
    "send": "Envoi manuel de secours",
    "report_hint": "Le JSON reste enregistré localement et peut être vérifié avant envoi.",
})
base._TEXT["en"].update({
    "done": "Diagnostic complete — the report can now be uploaded directly.",
    "output_title": "3 · Local report",
    "send": "Manual fallback",
    "report_hint": "The JSON remains stored locally and can be reviewed before upload.",
})


class UploadDiagnosticApp(base.DiagnosticApp):
    """Preserve the read-only diagnostic and add a separate upload step."""

    def __init__(self, root: tk.Tk) -> None:
        self.latest_reports: list[Path] = []
        self.uploaded_reports: set[Path] = set()
        self.upload_thread: threading.Thread | None = None
        self.upload_events: queue.Queue[tuple[Any, ...]] = queue.Queue()
        self.upload_window: tk.Toplevel | None = None
        self._receipts: list[dict[str, Any]] = []
        self._dialog: dict[str, Any] = {}
        super().__init__(root)
        self.root.geometry("920x650")
        self.root.minsize(860, 620)
        self.root.after(150, self._sync_upload_button)
        self.root.after(100, self._poll_upload_events)

    @property
    def u(self) -> dict[str, str]:
        return _TEXT[self.lang]

    def _build_ui(self) -> None:
        super()._build_ui()
        content = self.root.winfo_children()[0]
        children = content.winfo_children()
        card = self._card(content)
        opts: dict[str, Any] = {"fill": "x", "pady": (12, 0)}
        if children:
            opts["before"] = children[-1]
        card.pack(**opts)
        row = tk.Frame(card, bg=base._CARD)
        row.pack(fill="x", padx=18, pady=12)
        row.columnconfigure(0, weight=1)
        info = tk.Frame(row, bg=base._CARD)
        info.grid(row=0, column=0, sticky="ew", padx=(0, 16))
        tk.Label(info, text=self.u["title"], bg=base._CARD, fg=base._TEXT_COLOR,
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(fill="x")
        tk.Label(info, text=self.u["summary"], bg=base._CARD, fg=base._MUTED,
                 font=("Segoe UI", 8), wraplength=610, justify="left", anchor="w").pack(fill="x", pady=(3, 4))
        self.upload_status = tk.StringVar(value=self.u["waiting"])
        self.upload_status_label = tk.Label(info, textvariable=self.upload_status, bg=base._CARD,
                                            fg=base._MUTED, font=("Segoe UI", 8, "bold"), anchor="w")
        self.upload_status_label.pack(fill="x")
        self.upload_button = self._flat_button(row, self.u["button"], self._show_upload_dialog,
                                               primary=True, compact=True)
        self.upload_button.grid(row=0, column=1, sticky="e")
        self.upload_button.configure(state="disabled")

    @staticmethod
    def _snapshot(folder: Path) -> dict[Path, tuple[int, int]]:
        result: dict[Path, tuple[int, int]] = {}
        try:
            for path in folder.glob("*.json"):
                try:
                    st = path.stat()
                    result[path.resolve()] = (st.st_mtime_ns, st.st_size)
                except OSError:
                    pass
        except OSError:
            pass
        return result

    def _run_dump(self, folder: Path, host: str, monitor_sn: str) -> None:
        before = self._snapshot(folder)
        super()._run_dump(folder, host, monitor_sn)
        after = self._snapshot(folder)
        changed = [p for p, sig in after.items() if before.get(p) != sig]
        changed.sort(key=lambda p: after[p][0])
        if changed:
            self.latest_reports = changed
            self.uploaded_reports.difference_update(changed)

    def _start(self) -> None:
        if not (self.worker and self.worker.is_alive()):
            self.latest_reports = []
            self.uploaded_reports.clear()
            if hasattr(self, "upload_status"):
                self.upload_status.set(self.u["capturing"])
                self.upload_status_label.configure(fg=base._ACCENT)
        super()._start()

    def _remaining(self) -> list[Path]:
        return [p for p in self.latest_reports if p not in self.uploaded_reports and p.exists()]

    def _sync_upload_button(self) -> None:
        try:
            capturing = bool(self.worker and self.worker.is_alive())
            uploading = bool(self.upload_thread and self.upload_thread.is_alive())
            remaining = self._remaining()
            if capturing:
                state, text, fg = "disabled", self.u["capturing"], base._ACCENT
            elif uploading:
                state, text, fg = "disabled", self.upload_status.get(), base._ACCENT
            elif remaining:
                state, text, fg = "normal", self.u["ready"].format(count=len(remaining)), base._SUCCESS
            elif self.latest_reports:
                state, text, fg = "disabled", self.u["sent"], base._SUCCESS
            else:
                state, text, fg = "disabled", self.u["waiting"], base._MUTED
            self.upload_button.configure(state=state)
            self.upload_status.set(text)
            self.upload_status_label.configure(fg=fg)
        except tk.TclError:
            return
        finally:
            try:
                self.root.after(250, self._sync_upload_button)
            except tk.TclError:
                pass

    def _show_upload_dialog(self) -> None:
        paths = self._remaining()
        if not paths:
            messagebox.showinfo(APP_NAME, self.u["none"], parent=self.root)
            return
        if self.upload_window is not None:
            try:
                if self.upload_window.winfo_exists():
                    self.upload_window.lift(); self.upload_window.focus_force(); return
            except tk.TclError:
                pass

        win = tk.Toplevel(self.root)
        self.upload_window = win
        win.title(self.u["dialog"]); win.geometry("690x610"); win.minsize(620, 560)
        win.configure(bg=base._BG); win.transient(self.root)

        def close() -> None:
            if self.upload_thread and self.upload_thread.is_alive():
                messagebox.showinfo(APP_NAME, self.u["busy"], parent=win); return
            self.upload_window = None; win.destroy()
        win.protocol("WM_DELETE_WINDOW", close)

        card = self._card(win); card.pack(fill="both", expand=True, padx=18, pady=18)
        inner = tk.Frame(card, bg=base._CARD); inner.pack(fill="both", expand=True, padx=20, pady=18)
        self._label(inner, self.u["dialog"], 15, True).pack(fill="x")
        self._label(inner, self.u["privacy"], 9, False, muted=True, wrap=620).pack(fill="x", pady=(7, 14))
        self._label(inner, self.u["files"], 9, True).pack(fill="x")
        self._label(inner, "\n".join(f"• {p.name}" for p in paths), 8, False, wrap=620,
                    bg=base._SOFT_BLUE, padx=9, pady=7).pack(fill="x", pady=(4, 12))

        self._label(inner, self.u["tester"], 9, True).pack(fill="x")
        self._label(inner, self.u["tester_hint"], 8, False, muted=True).pack(fill="x", pady=(1, 4))
        tester = tk.StringVar(); tester_entry = tk.Entry(inner, textvariable=tester, relief="solid", bd=1, font=("Segoe UI", 9))
        tester_entry.pack(fill="x", ipady=6)

        self._label(inner, self.u["devices"], 9, True).pack(fill="x", pady=(12, 0))
        self._label(inner, self.u["devices_hint"], 8, False, muted=True).pack(fill="x", pady=(1, 4))
        devices = tk.Text(inner, height=4, wrap="word", relief="solid", bd=1, font=("Segoe UI", 9)); devices.pack(fill="x")

        consent = tk.BooleanVar(value=False)
        consent_box = tk.Checkbutton(inner, text=self.u["consent"], variable=consent, bg=base._CARD,
            fg=base._TEXT_COLOR, activebackground=base._CARD, activeforeground=base._TEXT_COLOR,
            selectcolor=base._CARD, font=("Segoe UI", 9, "bold"), justify="left", wraplength=610, anchor="w")
        consent_box.pack(fill="x", pady=(14, 8))
        status = tk.StringVar(value="")
        status_label = self._label(inner, "", 8, True, muted=True, wrap=610)
        status_label.configure(textvariable=status); status_label.pack(fill="x")

        buttons = tk.Frame(inner, bg=base._CARD); buttons.pack(fill="x", pady=(12, 0))
        send = self._flat_button(buttons, self.u["send"], lambda: self._begin_upload(
            paths, tester.get(), devices.get("1.0", "end"), consent.get()), primary=True, compact=True)
        send.pack(side="left"); send.configure(state="disabled")
        self._flat_button(buttons, self.u["cancel"], close, compact=True).pack(side="right")
        consent.trace_add("write", lambda *_: send.configure(state="normal" if consent.get() else "disabled"))
        self._dialog = {"status": status, "label": status_label, "send": send, "tester": tester_entry,
                        "devices": devices, "consent": consent_box, "consent_var": consent}
        win.update_idletasks()
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - win.winfo_width()) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - win.winfo_height()) // 2)
        win.geometry(f"+{x}+{y}"); win.lift(); win.focus_force()

    def _label(self, parent: tk.Misc, text: str, size: int, bold: bool, *, muted: bool = False,
               wrap: int | None = None, bg: str | None = None, padx: int = 0, pady: int = 0) -> tk.Label:
        return tk.Label(parent, text=text, bg=bg or base._CARD, fg=base._MUTED if muted else base._TEXT_COLOR,
                        font=("Segoe UI", size, "bold" if bold else "normal"), justify="left",
                        wraplength=wrap or 0, anchor="w", padx=padx, pady=pady)

    def _begin_upload(self, paths: list[Path], tester_name: str, devices_raw: str, consent: bool) -> None:
        if self.upload_thread and self.upload_thread.is_alive():
            return
        try:
            parsed = report_upload.parse_declared_devices(devices_raw)
            report_upload.build_payload({}, consent=consent, tester_name=tester_name, declared_devices=parsed)
        except report_upload.ReportUploadError as exc:
            messagebox.showerror(self.u["invalid"], str(exc), parent=self.upload_window or self.root); return
        pending = [p for p in paths if p not in self.uploaded_reports and p.exists()]
        if not pending:
            return
        for key in ("send", "tester", "devices", "consent"):
            self._dialog[key].configure(state="disabled")
        self._dialog["label"].configure(fg=base._ACCENT)
        self._receipts = []
        self.upload_thread = threading.Thread(target=self._upload_reports,
            args=(pending, tester_name.strip(), parsed), daemon=True)
        self.upload_thread.start()

    def _upload_reports(self, paths: list[Path], tester_name: str, devices: list[dict[str, Any]]) -> None:
        for current, path in enumerate(paths, 1):
            self.upload_events.put(("progress", current, len(paths)))
            try:
                receipt = report_upload.upload_file(path, consent=True, tester_name=tester_name,
                    declared_devices=devices, user_agent=f"TSUN-Local-Diagnostic/{APP_VERSION}")
            except report_upload.ReportUploadError as exc:
                self.upload_events.put(("error", str(exc))); return
            self.upload_events.put(("uploaded", path, receipt))
        self.upload_events.put(("complete",))

    def _restore_dialog(self) -> None:
        for key in ("tester", "devices", "consent"):
            try: self._dialog[key].configure(state="normal")
            except (KeyError, tk.TclError): pass
        try:
            enabled = self._dialog["consent_var"].get()
            self._dialog["send"].configure(state="normal" if enabled else "disabled")
        except (KeyError, tk.TclError): pass

    def _poll_upload_events(self) -> None:
        try:
            while True:
                event = self.upload_events.get_nowait(); kind = event[0]
                if kind == "progress":
                    self._dialog["status"].set(self.u["progress"].format(current=event[1], total=event[2]))
                elif kind == "uploaded":
                    self.uploaded_reports.add(Path(event[1])); self._receipts.append(dict(event[2]))
                elif kind == "error":
                    self._dialog["status"].set(self.u["error"].format(error=event[1]))
                    self._dialog["label"].configure(fg=base._DANGER); self._restore_dialog()
                elif kind == "complete":
                    ids = ", ".join(str(r.get("report_id", "?")) for r in self._receipts)
                    self._dialog["status"].set(self.u["complete"].format(ids=ids))
                    self._dialog["label"].configure(fg=base._SUCCESS); self._restore_dialog()
                    self._dialog["send"].configure(state="disabled")
        except queue.Empty:
            pass
        except (KeyError, tk.TclError):
            pass
        finally:
            try: self.root.after(100, self._poll_upload_events)
            except tk.TclError: pass


def main() -> int:
    internal_result = base._internal_update_mode()
    if internal_result is not None:
        return internal_result
    root = tk.Tk(); UploadDiagnosticApp(root); root.mainloop(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
