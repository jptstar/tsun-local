#!/usr/bin/env python3
# Copyright (C) 2026 Jean-Philippe TESTART (jptstar)
# SPDX-License-Identifier: GPL-3.0-or-later
"""TSUN Local Diagnostic 1.5.9 catalogue and post-upload link refinements."""

from __future__ import annotations

import re
import tkinter as tk
from urllib.parse import quote
import webbrowser

import tsun_diagnostic_desktop_v158 as previous

APP_NAME = previous.APP_NAME
APP_VERSION = "1.5.9"
MAX_DEVICE_ROWS = previous.MAX_DEVICE_ROWS
REPORTS_REPOSITORY_URL = "https://github.com/jptstar/tsun-local-reports"
SUNOLOGY_PLAY2_MODEL = "Sunology PLAY 2"

# Keep the portable self-updater/version checks aligned with this wrapper.
previous.APP_VERSION = APP_VERSION
previous.legacy.APP_VERSION = APP_VERSION
previous.legacy.base.APP_VERSION = APP_VERSION
previous.legacy.upload_app.APP_VERSION = APP_VERSION

# Sunology PLAY 2 uses TSUN hardware but is sold under the Sunology product name.
# Add it to the same searchable catalogue used by the ten compact declaration rows.
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
        "published": "Rapport envoyé — liens de consultation :",
        "open_published": "Voir exactement le rapport envoyé",
        "github_published": "Fichier enregistré sur GitHub :",
        "open_github": "Ouvrir le fichier sur GitHub",
        "github_private": (
            "Le dépôt GitHub est privé : ce lien GitHub nécessite un compte autorisé. "
            "Le lien de consultation ci-dessus permet au testeur de voir exactement le contenu envoyé."
        ),
        "link_missing": (
            "Le serveur n’a pas renvoyé de lien public de consultation. "
            "Le lien direct GitHub reste affiché ci-dessous."
        ),
    }
)
previous.legacy.upload_app._TEXT["en"].update(
    {
        "devices_hint": (
            "Up to 10 types. Type part of a model (e.g. MS, MP3000, PLAY, 800) "
            "to filter the list, then choose the quantity."
        ),
        "published": "Report uploaded — viewing links:",
        "open_published": "View exactly what was uploaded",
        "github_published": "File stored on GitHub:",
        "open_github": "Open file on GitHub",
        "github_private": (
            "The GitHub repository is private: the GitHub link requires an authorized account. "
            "The viewing link above lets the tester see exactly what was uploaded."
        ),
        "link_missing": (
            "The server did not return a public viewing link. "
            "The direct GitHub link is still shown below."
        ),
    }
)

_REPORT_ID_RE = re.compile(r"^TSL-(\d{4})(\d{2})(\d{2})-[A-F0-9]{8}$")


def github_report_url(receipt: dict[str, object]) -> str:
    """Return a deterministic GitHub blob URL for a successful upload receipt."""
    path = receipt.get("path")
    if not isinstance(path, str) or not path.strip():
        report_id = receipt.get("report_id")
        if not isinstance(report_id, str):
            return ""
        match = _REPORT_ID_RE.fullmatch(report_id)
        if match is None:
            return ""
        path = f"reports/{match.group(1)}/{match.group(2)}/{report_id}.json"

    normalized = path.strip().replace("\\", "/")
    if not normalized.startswith("reports/") or ".." in normalized.split("/"):
        return ""
    return f"{REPORTS_REPOSITORY_URL}/blob/main/{quote(normalized, safe='/-_.')}"


class CleanDiagnosticApp(previous.CleanDiagnosticApp):
    """Add Sunology catalogue support and always expose the stored report link."""

    def __init__(self, root: tk.Tk) -> None:
        self._last_report_link_signature = ""
        super().__init__(root)

    def _add_clickable_link(
        self,
        parent: tk.Frame,
        *,
        caption: str,
        url: str,
        button_text: str,
    ) -> None:
        base = previous.legacy.base
        tk.Label(
            parent,
            text=caption,
            bg=base._SOFT_GREEN,
            fg=base._SUCCESS,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
            padx=10,
            pady=4,
        ).pack(fill="x")
        label = tk.Label(
            parent,
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
        label.pack(fill="x")
        label.bind("<Button-1>", lambda _event, link=url: webbrowser.open(link))
        self._flat_button(
            parent,
            button_text,
            lambda link=url: webbrowser.open(link),
            compact=True,
        ).pack(anchor="w", padx=10, pady=(3, 6))

    def _sync_view_link(self) -> None:
        """Show the public receipt URL and always show the exact GitHub file URL."""
        base = previous.legacy.base
        try:
            if not self._receipts or self._view_link_host is None:
                return

            receipt = self._receipts[-1]
            public_candidate = receipt.get("view_url")
            public_url = (
                public_candidate
                if isinstance(public_candidate, str) and public_candidate.startswith("https://")
                else ""
            )
            github_url = github_report_url(receipt)
            signature = f"{public_url}|{github_url}"
            if signature == self._last_report_link_signature:
                return
            self._last_report_link_signature = signature
            self._view_link_url = public_url or github_url

            for child in self._view_link_host.winfo_children():
                child.destroy()

            tk.Label(
                self._view_link_host,
                text=self.u["published"],
                bg=base._SOFT_GREEN,
                fg=base._SUCCESS,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
                padx=10,
                pady=7,
            ).pack(fill="x")

            if public_url:
                self._add_clickable_link(
                    self._view_link_host,
                    caption=(
                        "Voir exactement ce qui a été envoyé :"
                        if self.lang == "fr"
                        else "View exactly what was uploaded:"
                    ),
                    url=public_url,
                    button_text=self.u["open_published"],
                )
            else:
                tk.Label(
                    self._view_link_host,
                    text=self.u["link_missing"],
                    bg=base._SOFT_GREEN,
                    fg=base._MUTED,
                    font=("Segoe UI", 8, "bold"),
                    justify="left",
                    wraplength=610,
                    anchor="w",
                    padx=10,
                    pady=5,
                ).pack(fill="x")

            if github_url:
                self._add_clickable_link(
                    self._view_link_host,
                    caption=self.u["github_published"],
                    url=github_url,
                    button_text=self.u["open_github"],
                )
                tk.Label(
                    self._view_link_host,
                    text=self.u["github_private"],
                    bg=base._SOFT_GREEN,
                    fg=base._MUTED,
                    font=("Segoe UI", 7),
                    justify="left",
                    wraplength=610,
                    anchor="w",
                    padx=10,
                    pady=(0, 8),
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
    internal_result = previous.legacy.base._internal_update_mode()
    if internal_result is not None:
        return internal_result
    root = tk.Tk()
    CleanDiagnosticApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
