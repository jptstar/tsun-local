from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[2]
path = ROOT / "tools" / "tsun_diagnostic_gui.py"
text = path.read_text(encoding="utf-8")

text = text.replace('APP_VERSION = "1.4.1"', 'APP_VERSION = "1.4.2"', 1)

fr_anchor = '        "folder_error": "Impossible d\'utiliser le dossier de sortie sélectionné.",\n        "footer": "Moteur tsun_dump.py v{dump} · Interface v{gui} · Lecture seule",\n'
fr_replacement = '        "folder_error": "Impossible d\'utiliser le dossier de sortie sélectionné.",\n        "update_checking": "Vérification des mises à jour…",\n        "update_current": "Application à jour.",\n        "update_found": "Mise à jour v{version} disponible — téléchargement…",\n        "update_ready": "Mise à jour téléchargée et vérifiée — redémarrage…",\n        "update_failed": "Vérification de mise à jour impossible — cette version reste utilisable.",\n        "update_disabled": "Vérification automatique des mises à jour désactivée.",\n        "footer": "Moteur tsun_dump.py v{dump} · Interface v{gui} · Lecture seule",\n'
if fr_anchor not in text:
    raise SystemExit("French translation anchor not found")
text = text.replace(fr_anchor, fr_replacement, 1)

en_anchor = '        "folder_error": "The selected output folder cannot be used.",\n        "footer": "tsun_dump.py engine v{dump} · GUI v{gui} · Read-only",\n'
en_replacement = '        "folder_error": "The selected output folder cannot be used.",\n        "update_checking": "Checking for updates…",\n        "update_current": "Application is up to date.",\n        "update_found": "Update v{version} available — downloading…",\n        "update_ready": "Update downloaded and verified — restarting…",\n        "update_failed": "Update check failed — this version remains usable.",\n        "update_disabled": "Automatic update check disabled.",\n        "footer": "tsun_dump.py engine v{dump} · GUI v{gui} · Read-only",\n'
if en_anchor not in text:
    raise SystemExit("English translation anchor not found")
text = text.replace(en_anchor, en_replacement, 1)

state_anchor = '        self.output_dir = tk.StringVar(value=str(self._default_output_dir()))\n        self.status = tk.StringVar(value=self.t["ready"])\n\n        self._configure_ttk()\n'
state_replacement = '        self.output_dir = tk.StringVar(value=str(self._default_output_dir()))\n        self.status = tk.StringVar(value=self.t["ready"])\n        self.update_status = tk.StringVar(value=self.t["update_checking"])\n        self.update_busy = False\n\n        self._configure_ttk()\n'
if state_anchor not in text:
    raise SystemExit("State anchor not found")
text = text.replace(state_anchor, state_replacement, 1)

init_anchor = '        self.confirm_disabled.trace_add("write", self._sync_run_button)\n        self.root.after(100, self._poll_events)\n'
init_replacement = '        self.confirm_disabled.trace_add("write", self._sync_run_button)\n        self.root.after(100, self._poll_events)\n        self.root.after(250, self._start_update_check)\n'
if init_anchor not in text:
    raise SystemExit("Init scheduling anchor not found")
text = text.replace(init_anchor, init_replacement, 1)

header_anchor = '        tk.Label(\n            header,\n            text=self.t["subtitle"],\n            bg=_BG,\n            fg=_MUTED,\n            font=("Segoe UI", 9),\n            anchor="w",\n        ).pack(fill="x", pady=(4, 0))\n\n        main = tk.Frame(content, bg=_BG)\n'
header_replacement = '        tk.Label(\n            header,\n            text=self.t["subtitle"],\n            bg=_BG,\n            fg=_MUTED,\n            font=("Segoe UI", 9),\n            anchor="w",\n        ).pack(fill="x", pady=(4, 0))\n        self.update_label = tk.Label(\n            header,\n            textvariable=self.update_status,\n            bg=_BG,\n            fg=_ACCENT,\n            font=("Segoe UI", 9, "bold"),\n            anchor="w",\n        )\n        self.update_label.pack(fill="x", pady=(5, 0))\n\n        main = tk.Frame(content, bg=_BG)\n'
if header_anchor not in text:
    raise SystemExit("Header anchor not found")
text = text.replace(header_anchor, header_replacement, 1)

sync_anchor = '    def _sync_run_button(self, *_args: Any) -> None:\n        if self.worker and self.worker.is_alive():\n            self.run_button.configure(state="disabled")\n            return\n        state = "normal" if self.confirm_disabled.get() else "disabled"\n        self.run_button.configure(state=state)\n\n'
sync_replacement = '    def _sync_run_button(self, *_args: Any) -> None:\n        if self.update_busy or (self.worker and self.worker.is_alive()):\n            self.run_button.configure(state="disabled")\n            return\n        state = "normal" if self.confirm_disabled.get() else "disabled"\n        self.run_button.configure(state=state)\n\n    def _start_update_check(self) -> None:\n        """Start a visible, non-blocking update check after the window is shown."""\n        if (\n            os.name != "nt"\n            or not getattr(sys, "frozen", False)\n            or "--no-update" in sys.argv\n        ):\n            self.update_busy = False\n            self.update_status.set(self.t["update_disabled"])\n            self.update_label.configure(fg=_MUTED)\n            self._sync_run_button()\n            return\n\n        self.update_busy = True\n        self.update_status.set(self.t["update_checking"])\n        self.update_label.configure(fg=_ACCENT)\n        self._sync_run_button()\n        threading.Thread(target=self._run_update_check, daemon=True).start()\n\n    def _run_update_check(self) -> None:\n        """Check, download and verify a Windows update while reporting progress."""\n        try:\n            manifest = tsun_dump.fetch_update_manifest()\n            update = tsun_dump.select_update_component(\n                manifest,\n                tsun_dump.UPDATE_COMPONENT_WINDOWS_GUI,\n                APP_VERSION,\n            )\n            embedded_dump_update = tsun_dump.select_update_component(\n                manifest,\n                tsun_dump.UPDATE_COMPONENT_DUMP,\n                tsun_dump.TOOL_VERSION,\n            )\n            if update is None and embedded_dump_update is not None:\n                update = tsun_dump.select_update_component(\n                    manifest,\n                    tsun_dump.UPDATE_COMPONENT_WINDOWS_GUI,\n                    "0.0.0",\n                )\n            if update is None:\n                self.events.put(("update_current",))\n                return\n\n            version = update["version"]\n            self.events.put(("update_downloading", version))\n            destination = Path(tempfile.gettempdir()) / (\n                f"TSUN-Local-Diagnostic-update-{version}-{os.getpid()}.exe"\n            )\n            tsun_dump.download_verified_update(update, destination)\n            self.events.put(("update_ready", destination, version))\n        except Exception as exc:\n            self.events.put(("update_failed", type(exc).__name__))\n\n    def _apply_downloaded_update(self, destination: Path) -> None:\n        """Hand off replacement to the verified updater, then close this process."""\n        try:\n            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)\n            subprocess.Popen(\n                [\n                    str(destination),\n                    _INTERNAL_UPDATE_SWITCH,\n                    str(Path(sys.executable).resolve()),\n                ],\n                close_fds=True,\n                creationflags=creationflags,\n            )\n        except OSError:\n            self.update_busy = False\n            self.update_status.set(self.t["update_failed"])\n            self.update_label.configure(fg=_DANGER)\n            self._sync_run_button()\n            return\n        self.root.destroy()\n\n'
if sync_anchor not in text:
    raise SystemExit("Run-button anchor not found")
text = text.replace(sync_anchor, sync_replacement, 1)

poll_anchor = '                if kind == "log":\n                    self._append_log(str(event[1]))\n                elif kind == "status":\n'
poll_replacement = '                if kind == "log":\n                    self._append_log(str(event[1]))\n                elif kind == "update_current":\n                    self.update_busy = False\n                    self.update_status.set(self.t["update_current"])\n                    self.update_label.configure(fg=_SUCCESS)\n                    self._sync_run_button()\n                elif kind == "update_downloading":\n                    self.update_status.set(\n                        self.t["update_found"].format(version=str(event[1]))\n                    )\n                    self.update_label.configure(fg=_ACCENT)\n                elif kind == "update_ready":\n                    destination = Path(str(event[1]))\n                    self.update_status.set(self.t["update_ready"])\n                    self.update_label.configure(fg=_SUCCESS)\n                    self.root.after(650, lambda p=destination: self._apply_downloaded_update(p))\n                elif kind == "update_failed":\n                    self.update_busy = False\n                    self.update_status.set(self.t["update_failed"])\n                    self.update_label.configure(fg=_DANGER)\n                    self._sync_run_button()\n                    self._append_log(f"Update check failed: {event[1]}\\n")\n                elif kind == "status":\n'
if poll_anchor not in text:
    raise SystemExit("Event polling anchor not found")
text = text.replace(poll_anchor, poll_replacement, 1)

main_anchor = 'def main() -> int:\n    internal_result = _internal_update_mode()\n    if internal_result is not None:\n        return internal_result\n    if _maybe_auto_update_windows():\n        return 0\n\n    root = tk.Tk()\n'
main_replacement = 'def main() -> int:\n    internal_result = _internal_update_mode()\n    if internal_result is not None:\n        return internal_result\n\n    # Show the application immediately. Update checks are performed visibly\n    # from the GUI so a double-click never appears to do nothing.\n    root = tk.Tk()\n'
if main_anchor not in text:
    raise SystemExit("Main startup anchor not found")
text = text.replace(main_anchor, main_replacement, 1)

path.write_text(text, encoding="utf-8")
