#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Clean four-step TSUN Local Diagnostic desktop layout.

Steps 1-2 keep the existing read-only diagnostic workflow on the left.
Step 3 is the recommended direct upload on the right. Step 4 is an optional
manual e-mail fallback spanning the full width at the bottom.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import tkinter as tk
from tkinter import messagebox
import webbrowser

import tsun_diagnostic_app as upload_app
import tsun_diagnostic_gui as base

APP_NAME = base.APP_NAME
APP_VERSION = "1.5.4"

MAGIC_TEST_HOST = "89:89:89:89"
MAGIC_TEST_SN = "89898989"

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
        "published": "Rapport publié — lien de consultation :",
        "open_published": "Ouvrir le rapport publié",
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
        "published": "Report published — viewing link:",
        "open_published": "Open published report",
    }
)


class CleanDiagnosticApp(upload_app.UploadDiagnosticApp):
    """Present the diagnostic as four visually ordered steps."""

    def __init__(self, root: tk.Tk) -> None:
        self._view_link_host: tk.Frame | None = None
        self._view_link_url = ""
        self._view_link_label: tk.Label | None = None
        super().__init__(root)
        self.root.geometry("980x700")
        self.root.minsize(920, 650)
        self.host.trace_add("write", self._sync_run_button)
        self.monitor_sn.trace_add("write", self._sync_run_button)
        self.root.after(150, self._sync_view_link)

    def _build_ui(self) -> None:
        # Build the proven diagnostic UI first, then reorganize only presentation.
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

        # The base UI puts its manual-report card in the right column. Replace it
        # with step 3 there, then rebuild step 4 as a full-width optional footer.
        old_manual_cards = right.winfo_children()
        for widget in old_manual_cards:
            widget.destroy()

        self._build_direct_step(right)
        self._build_manual_step(content, bottom_toolbar)

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

    def _show_upload_dialog(self) -> None:
        super()._show_upload_dialog()
        win = self.upload_window
        if win is None:
            return
        try:
            win.geometry("690x650")
            card = win.winfo_children()[0]
            inner = card.winfo_children()[0]
        except (IndexError, tk.TclError):
            return

        if self._view_link_host is not None:
            try:
                if self._view_link_host.winfo_exists():
                    return
            except tk.TclError:
                pass

        self._view_link_host = tk.Frame(inner, bg=base._SOFT_GREEN)
        self._view_link_host.pack(fill="x", pady=(10, 0))
        self._view_link_host.pack_forget()

    def _sync_view_link(self) -> None:
        try:
            url = ""
            if self._receipts:
                candidate = self._receipts[-1].get("view_url")
                if isinstance(candidate, str) and candidate.startswith("https://"):
                    url = candidate

            if url and url != self._view_link_url and self._view_link_host is not None:
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
                    pady=6,
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
                    "<Button-1>", lambda _event, link=url: webbrowser.open(link)
                )
                self._flat_button(
                    self._view_link_host,
                    self.u["open_published"],
                    lambda link=url: webbrowser.open(link),
                    compact=True,
                ).pack(anchor="w", padx=10, pady=(5, 9))
                self._view_link_host.pack(fill="x", pady=(10, 0))
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
