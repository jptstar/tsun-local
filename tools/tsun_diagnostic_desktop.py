#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Clean four-step TSUN Local Diagnostic desktop layout.

Steps 1-2 keep the existing read-only diagnostic workflow on the left.
Step 3 is the recommended direct upload on the right. Step 4 is an optional
manual e-mail fallback spanning the full width at the bottom.
"""

from __future__ import annotations

import tkinter as tk

import tsun_diagnostic_app as upload_app
import tsun_diagnostic_gui as base

APP_NAME = base.APP_NAME
APP_VERSION = "1.5.2"

base.APP_VERSION = APP_VERSION
upload_app.APP_VERSION = APP_VERSION

base._TEXT["fr"].update(
    {
        "done": "Diagnostic terminé — vous pouvez maintenant envoyer le rapport.",
        "output_title": "4 · Envoi manuel par e-mail",
        "send": "Adresse e-mail",
        "report_hint": "Solution optionnelle si l’envoi direct n’est pas disponible.",
    }
)
base._TEXT["en"].update(
    {
        "done": "Diagnostic complete — you can now send the report.",
        "output_title": "4 · Manual report by e-mail",
        "send": "E-mail address",
        "report_hint": "Optional fallback if direct upload is not available.",
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
    """Present the diagnostic as four visually ordered steps."""

    def __init__(self, root: tk.Tk) -> None:
        super().__init__(root)
        self.root.geometry("980x700")
        self.root.minsize(920, 650)

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
            text="OPTIONNEL" if self.lang == "fr" else "OPTIONAL",
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
            wraplength=250,
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
