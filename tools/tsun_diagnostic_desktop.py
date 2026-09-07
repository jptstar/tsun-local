#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Clean four-step TSUN Local Diagnostic desktop layout.

Steps 1-2 keep the existing read-only diagnostic workflow. Step 3 is the
recommended explicit-consent direct upload. Step 4 keeps manual e-mail as a
clearly separated fallback.
"""

from __future__ import annotations

import tkinter as tk

import tsun_diagnostic_app as upload_app
import tsun_diagnostic_gui as base

APP_NAME = base.APP_NAME
APP_VERSION = "1.5.1"

base.APP_VERSION = APP_VERSION
upload_app.APP_VERSION = APP_VERSION

base._TEXT["fr"].update(
    {
        "done": "Diagnostic terminé — vous pouvez maintenant envoyer le rapport.",
        "output_title": "4 · Envoi manuel par e-mail",
        "send": "Solution de secours : envoyez le JSON à",
        "report_hint": (
            "Le JSON reste enregistré localement. Utilisez l’envoi manuel si "
            "l’envoi direct n’est pas disponible."
        ),
    }
)
base._TEXT["en"].update(
    {
        "done": "Diagnostic complete — you can now send the report.",
        "output_title": "4 · Manual report by e-mail",
        "send": "Fallback option: send the JSON to",
        "report_hint": (
            "The JSON remains stored locally. Use manual e-mail if direct upload "
            "is not available."
        ),
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
    }
)


class CleanDiagnosticApp(upload_app.UploadDiagnosticApp):
    """Present the diagnostic as four compact, ordered steps."""

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.root.geometry("960x650")
        self.root.minsize(900, 610)

    def _build_ui(self) -> None:
        base.DiagnosticApp._build_ui(self)

        content = self.root.winfo_children()[0]
        content_children = content.winfo_children()
        if len(content_children) < 2:
            raise RuntimeError("unexpected diagnostic UI structure")
        main = content_children[1]
        columns = main.winfo_children()
        if len(columns) < 2:
            raise RuntimeError("unexpected diagnostic column structure")
        right = columns[1]
        manual_children = right.winfo_children()
        if not manual_children:
            raise RuntimeError("manual report card is missing")
        manual_card = manual_children[0]

        direct_card = self._card(right)
        direct_card.pack(fill="x", pady=(0, 12), before=manual_card)
        direct_inner = tk.Frame(direct_card, bg=base._CARD)
        direct_inner.pack(fill="x", padx=18, pady=15)

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
            font=("Segoe UI", 8),
            justify="left",
            wraplength=385,
            anchor="w",
        ).pack(fill="x", pady=(6, 10))

        action_row = tk.Frame(direct_inner, bg=base._CARD)
        action_row.pack(fill="x")
        action_row.columnconfigure(0, weight=1)

        self.upload_status = tk.StringVar(value=self.u["waiting"])
        self.upload_status_label = tk.Label(
            action_row,
            textvariable=self.upload_status,
            bg=base._CARD,
            fg=base._MUTED,
            font=("Segoe UI", 8, "bold"),
            justify="left",
            wraplength=235,
            anchor="w",
        )
        self.upload_status_label.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.upload_button = self._flat_button(
            action_row,
            self.u["button"],
            self._show_upload_dialog,
            primary=True,
            compact=True,
        )
        self.upload_button.grid(row=0, column=1, sticky="e")
        self.upload_button.configure(state="disabled")


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
