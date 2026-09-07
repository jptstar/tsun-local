#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""TSUN Local Diagnostic 1.5.10 public post-upload report links."""

from __future__ import annotations

import tkinter as tk
import webbrowser

import tsun_diagnostic_desktop_v158 as previous

APP_NAME = previous.APP_NAME
APP_VERSION = "1.5.10"
MAX_DEVICE_ROWS = previous.MAX_DEVICE_ROWS
PROJECT_URL = previous.legacy.PROJECT_URL
COPYRIGHT_TEXT = previous.legacy.COPYRIGHT_TEXT
SUNOLOGY_PLAY2_MODEL = "Sunology PLAY 2"

# Preserve the public helpers introduced in 1.5.8.
load_upload_profile = previous.load_upload_profile
save_upload_profile = previous.save_upload_profile
filter_microinverter_models = previous.filter_microinverter_models

# Keep the portable self-updater/version checks aligned with this wrapper.
previous.APP_VERSION = APP_VERSION
previous.legacy.APP_VERSION = APP_VERSION
previous.legacy.base.APP_VERSION = APP_VERSION
previous.legacy.upload_app.APP_VERSION = APP_VERSION

# Sunology PLAY 2 uses TSUN hardware but is sold under the Sunology product name.
if SUNOLOGY_PLAY2_MODEL not in previous.legacy.upload_app.TSUN_MICROINVERTER_MODELS:
    previous.legacy.upload_app.TSUN_MICROINVERTER_MODELS = (
        *previous.legacy.upload_app.TSUN_MICROINVERTER_MODELS,
        SUNOLOGY_PLAY2_MODEL,
    )

previous.legacy.upload_app._TEXT["fr"].update(
    {
        "devices_hint": (
            "Jusqu’à 10 types. Tapez une partie du modèle (ex. MS, MP3000, PLAY, 800) "
            "pour filtrer la liste, puis choisissez la quantité."
        ),
        "published": "✓ Rapport(s) envoyé(s) avec succès",
        "open_published": "Ouvrir le rapport",
        "link_missing": (
            "Rapport envoyé, mais le serveur n’a pas retourné de lien de consultation."
        ),
    }
)
previous.legacy.upload_app._TEXT["en"].update(
    {
        "devices_hint": (
            "Up to 10 types. Type part of a model (e.g. MS, MP3000, PLAY, 800) "
            "to filter the list, then choose the quantity."
        ),
        "published": "✓ Report(s) uploaded successfully",
        "open_published": "Open report",
        "link_missing": (
            "Report uploaded, but the server did not return a viewing link."
        ),
    }
)


class CleanDiagnosticApp(previous.CleanDiagnosticApp):
    """Expose only per-report public viewing links, including on the main page."""

    def __init__(self, root: tk.Tk) -> None:
        self._main_report_links_host: tk.Frame | None = None
        self._last_report_link_signature = ""
        super().__init__(root)

    def _build_direct_step(self, right: tk.Frame) -> None:
        """Keep step 3 compact and reserve a persistent success area below upload."""
        super()._build_direct_step(right)
        base = previous.legacy.base
        parent = self.upload_button.master
        self._main_report_links_host = tk.Frame(parent, bg=base._SOFT_GREEN)
        self._main_report_links_host.pack(fill="x", pady=(10, 0))
        self._main_report_links_host.pack_forget()

    @staticmethod
    def _public_receipts(receipts: list[dict[str, object]]) -> list[tuple[str, str]]:
        """Return successful report IDs and their private-token public view URLs."""
        result: list[tuple[str, str]] = []
        for receipt in receipts:
            report_id = str(receipt.get("report_id", "?")).strip() or "?"
            candidate = receipt.get("view_url")
            url = (
                candidate
                if isinstance(candidate, str) and candidate.startswith("https://")
                else ""
            )
            result.append((report_id, url))
        return result

    def _render_report_links(self, host: tk.Frame, reports: list[tuple[str, str]]) -> None:
        base = previous.legacy.base
        for child in host.winfo_children():
            child.destroy()

        tk.Label(
            host,
            text=self.u["published"],
            bg=base._SOFT_GREEN,
            fg=base._SUCCESS,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
            padx=10,
            pady=7,
        ).pack(fill="x")

        for report_id, url in reports:
            row = tk.Frame(host, bg=base._SOFT_GREEN)
            row.pack(fill="x", padx=10, pady=(0, 7))
            tk.Label(
                row,
                text=report_id,
                bg=base._SOFT_GREEN,
                fg=base._TEXT_COLOR,
                font=("Segoe UI", 8, "bold"),
                anchor="w",
            ).pack(fill="x")

            if url:
                link = tk.Label(
                    row,
                    text=url,
                    bg=base._SOFT_GREEN,
                    fg=base._ACCENT,
                    font=("Segoe UI", 8, "underline"),
                    cursor="hand2",
                    justify="left",
                    wraplength=390,
                    anchor="w",
                )
                link.pack(fill="x", pady=(2, 3))
                link.bind("<Button-1>", lambda _event, target=url: webbrowser.open(target))
                self._flat_button(
                    row,
                    self.u["open_published"],
                    lambda target=url: webbrowser.open(target),
                    compact=True,
                ).pack(anchor="w")
            else:
                tk.Label(
                    row,
                    text=self.u["link_missing"],
                    bg=base._SOFT_GREEN,
                    fg=base._MUTED,
                    font=("Segoe UI", 8),
                    justify="left",
                    wraplength=390,
                    anchor="w",
                ).pack(fill="x", pady=(2, 0))

        host.pack(fill="x", pady=(7, 0))

    def _sync_view_link(self) -> None:
        """Show every upload receipt without exposing the private reports repository."""
        try:
            reports = self._public_receipts(self._receipts)
            signature = "|".join(f"{report_id}:{url}" for report_id, url in reports)
            if reports and signature != self._last_report_link_signature:
                self._last_report_link_signature = signature
                self._view_link_url = next((url for _report_id, url in reports if url), "")

                # Upload dialog: useful before the user closes it.
                if self._view_link_host is not None:
                    self._render_report_links(self._view_link_host, reports)

                # Main page, step 3: remains visible after the upload dialog is closed.
                if self._main_report_links_host is not None:
                    self._render_report_links(self._main_report_links_host, reports)
        except tk.TclError:
            pass
        finally:
            try:
                self.root.after(200, self._sync_view_link)
            except tk.TclError:
                pass


def main() -> int:
    internal_result = previous.legacy.base._internal_update_mode()
    if internal_result is not None:
        return internal_result
    root = tk.Tk()
    CleanDiagnosticApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
