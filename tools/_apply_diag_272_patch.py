from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one match in {path}: {old[:80]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    dump = ROOT / "tools" / "tsun_dump.py"
    gui = ROOT / "tools" / "tsun_diagnostic_gui.py"
    tests = ROOT / "tests" / "test_tsun_dump_tool.py"

    replace_once(dump, 'TOOL_VERSION = "2.7.1"', 'TOOL_VERSION = "2.7.2"')
    replace_once(
        dump,
        'LOGGER_PROFILE_PATHS = ("/hide_set_edit.html",)\nLOGGER_WEB_CAPTURE_PATHS = (*LOGGER_STATUS_PATHS, *LOGGER_PROFILE_PATHS)',
        'LOGGER_PROFILE_PATHS = ("/hide_set_edit.html",)\n'
        'LOGGER_RESEARCH_PATHS = (\n'
        '    "/wireless.html",\n'
        '    "/wizard.html",\n'
        '    "/remote.html",\n'
        '    "/update.html",\n'
        '    "/invupdate.html",\n'
        ')\n'
        'LOGGER_WEB_CAPTURE_PATHS = (\n'
        '    *LOGGER_STATUS_PATHS,\n'
        '    *LOGGER_PROFILE_PATHS,\n'
        '    *LOGGER_RESEARCH_PATHS,\n'
        ')',
    )

    marker = '''class _LocalLinkParser(HTMLParser):\n    """Collect navigation targets from local logger HTML without executing anything."""\n'''
    insertion = r'''class _WebInterfaceParser(HTMLParser):
    """Summarize forms and event hooks without submitting or executing them."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[dict[str, Any]] = []
        self.script_sources: list[str] = []
        self.handlers: set[str] = set()
        self._current_form: dict[str, Any] | None = None

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {name.lower(): value or "" for name, value in attrs}

    def _collect_handlers(self, attrs: dict[str, str]) -> None:
        for key in ("onclick", "onsubmit", "onchange"):
            value = attrs.get(key, "")
            for match in re.finditer(r"\b([A-Za-z_$][A-Za-z0-9_$]*)\s*\(", value):
                self.handlers.add(match.group(1))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = self._attrs(attrs)
        self._collect_handlers(attributes)

        if tag == "script" and attributes.get("src"):
            self.script_sources.append(attributes["src"])
            return

        if tag == "form":
            form = {
                "method": (attributes.get("method") or "get").lower(),
                "action_raw": attributes.get("action") or "",
                "enctype": (attributes.get("enctype") or "").lower() or None,
                "fields": [],
            }
            self.forms.append(form)
            self._current_form = form
            return

        if self._current_form is None or tag not in ("input", "select", "textarea", "button"):
            return
        field_name = attributes.get("name") or attributes.get("id") or ""
        if not field_name or len(field_name) > 80:
            return
        field_type = attributes.get("type") or tag
        item = {"name": field_name, "type": field_type.lower()}
        if item not in self._current_form["fields"]:
            self._current_form["fields"].append(item)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "form":
            self._current_form = None


def _safe_same_logger_endpoint(value: str, current_path: str, host: str) -> str | None:
    """Normalize a same-logger endpoint for passive reporting only."""
    value = value.strip()
    if not value or value.startswith(("#", "javascript:")):
        return None
    try:
        target = urlsplit(urljoin(f"http://{host}{current_path}", value))
        port = target.port
    except ValueError:
        return None
    if target.scheme.lower() != "http" or target.hostname != host or port not in (None, 80):
        return None
    path = target.path or "/"
    if not path.startswith("/") or len(path) > 192:
        return None
    return path


def summarize_web_interface_read_only(
    document: str, current_path: str, host: str
) -> dict[str, Any]:
    """Extract passive form/endpoint metadata without requests, scripts or uploads."""
    parser = _WebInterfaceParser()
    try:
        parser.feed(document)
        parser.close()
    except (ValueError, TypeError):
        return {
            "path": current_path,
            "forms": [],
            "script_paths": [],
            "javascript_handlers": [],
            "candidate_local_endpoints": [],
        }

    forms: list[dict[str, Any]] = []
    endpoints: set[str] = set()
    for form in parser.forms:
        action = _safe_same_logger_endpoint(
            str(form.pop("action_raw", "")), current_path, host
        )
        if action:
            endpoints.add(action)
        forms.append({**form, "action": action})

    script_paths: list[str] = []
    for source in parser.script_sources:
        path = _safe_same_logger_endpoint(source, current_path, host)
        if path and path not in script_paths:
            script_paths.append(path)

    # Extract only quoted same-device path literals from JavaScript/HTML. Values,
    # credentials and payloads are deliberately ignored.
    for match in re.finditer(
        r"[\"']([^\"']{1,160}(?:\.cgi|\.asp|\.html?|\.shtml))[\"']",
        document,
        re.IGNORECASE,
    ):
        path = _safe_same_logger_endpoint(match.group(1), current_path, host)
        if path:
            endpoints.add(path)

    return {
        "path": current_path,
        "forms": forms,
        "script_paths": script_paths,
        "javascript_handlers": sorted(parser.handlers),
        "candidate_local_endpoints": sorted(endpoints),
        "read_only": True,
        "form_submission_performed": False,
        "javascript_executed": False,
        "upload_performed": False,
        "reboot_performed": False,
    }


'''
    text = dump.read_text(encoding="utf-8")
    if text.count(marker) != 1:
        raise RuntimeError("LocalLinkParser marker not found exactly once")
    dump.write_text(text.replace(marker, insertion + marker, 1), encoding="utf-8")

    replace_once(
        dump,
        '    pages: list[dict[str, Any]] = []\n    summary: dict[str, Any] = {',
        '    pages: list[dict[str, Any]] = []\n'
        '    interface_analysis: list[dict[str, Any]] = []\n'
        '    summary: dict[str, Any] = {',
    )
    replace_once(
        dump,
        '            sanitized = anonymize_web_document(document)\n            digest = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()',
        '            interface = summarize_web_interface_read_only(document, path, host)\n'
        '            if (\n'
        '                interface["forms"]\n'
        '                or interface["script_paths"]\n'
        '                or interface["javascript_handlers"]\n'
        '                or path in LOGGER_RESEARCH_PATHS\n'
        '            ):\n'
        '                interface_analysis.append(interface)\n\n'
        '            sanitized = anonymize_web_document(document)\n'
        '            digest = hashlib.sha256(sanitized.encode("utf-8")).hexdigest()',
    )
    replace_once(
        dump,
        '        "summary": summary,\n        "pages": pages,\n        "privacy": {',
        '        "summary": summary,\n'
        '        "interface_analysis": interface_analysis,\n'
        '        "pages": pages,\n'
        '        "privacy": {',
    )
    replace_once(
        dump,
        '            "form_submission_performed": False,\n            "max_page_paths": MAX_LOGGER_WEB_PATHS,',
        '            "form_submission_performed": False,\n'
        '            "javascript_executed": False,\n'
        '            "firmware_upload_performed": False,\n'
        '            "logger_reboot_performed": False,\n'
        '            "max_page_paths": MAX_LOGGER_WEB_PATHS,',
    )

    replace_once(gui, 'APP_VERSION = "1.4.0"', 'APP_VERSION = "1.4.1"')
    old_updater = '''    try:\n        update = tsun_dump.check_for_update(\n            tsun_dump.UPDATE_COMPONENT_WINDOWS_GUI,\n            APP_VERSION,\n        )\n        if update is None:\n            return False\n        destination = Path(tempfile.gettempdir()) / (\n'''
    new_updater = '''    try:\n        manifest = tsun_dump.fetch_update_manifest()\n        update = tsun_dump.select_update_component(\n            manifest,\n            tsun_dump.UPDATE_COMPONENT_WINDOWS_GUI,\n            APP_VERSION,\n        )\n        embedded_dump_update = tsun_dump.select_update_component(\n            manifest,\n            tsun_dump.UPDATE_COMPONENT_DUMP,\n            tsun_dump.TOOL_VERSION,\n        )\n        if update is None and embedded_dump_update is not None:\n            # The EXE bundles tsun_dump.py. Re-download the current Windows asset\n            # whenever the embedded engine is older, even if the GUI version did\n            # not otherwise change.\n            update = tsun_dump.select_update_component(\n                manifest,\n                tsun_dump.UPDATE_COMPONENT_WINDOWS_GUI,\n                "0.0.0",\n            )\n        if update is None:\n            return False\n        destination = Path(tempfile.gettempdir()) / (\n'''
    replace_once(gui, old_updater, new_updater)

    replace_once(tests, 'self.assertEqual(TOOL.TOOL_VERSION, "2.7.1")', 'self.assertEqual(TOOL.TOOL_VERSION, "2.7.2")')
    replace_once(
        tests,
        '    def test_dns_probe_command_is_get_only(self) -> None:\n',
        '''    def test_research_capture_paths_include_network_and_upgrade_pages(self) -> None:\n        self.assertEqual(len(TOOL.LOGGER_WEB_CAPTURE_PATHS), 10)\n        for path in (\n            "/wireless.html",\n            "/wizard.html",\n            "/remote.html",\n            "/update.html",\n            "/invupdate.html",\n        ):\n            self.assertIn(path, TOOL.LOGGER_WEB_CAPTURE_PATHS)\n\n    def test_web_interface_summary_is_passive_and_privacy_safe(self) -> None:\n        document = (\n            '<form method="post" enctype="multipart/form-data" action="upgrade.cgi" '\n            'onsubmit="return checkUpgrade()">'\n            '<input type="file" name="firmware_file">'\n            '<input type="hidden" name="ssid" value="SecretWifi">'\n            '<button type="submit" onclick="startUpgrade()">Upload</button>'\n            '</form>'\n            '<script src="helper.js"></script>'\n        )\n        summary = TOOL.summarize_web_interface_read_only(\n            document, "/update.html", "192.168.1.25"\n        )\n        self.assertTrue(summary["read_only"])\n        self.assertFalse(summary["form_submission_performed"])\n        self.assertFalse(summary["javascript_executed"])\n        self.assertFalse(summary["upload_performed"])\n        self.assertEqual(summary["forms"][0]["method"], "post")\n        self.assertEqual(summary["forms"][0]["action"], "/upgrade.cgi")\n        self.assertIn(\n            {"name": "firmware_file", "type": "file"},\n            summary["forms"][0]["fields"],\n        )\n        self.assertIn("checkUpgrade", summary["javascript_handlers"])\n        self.assertIn("startUpgrade", summary["javascript_handlers"])\n        self.assertNotIn("SecretWifi", repr(summary))\n\n    def test_dns_probe_command_is_get_only(self) -> None:\n''',
    )

    for relative in (
        "README.md",
        "tools/README.md",
        "docs/HARDWARE_DUMP.md",
        "docs/test-your-inverter.html",
    ):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        text = text.replace("Windows GUI **1.4.0** · dump engine **2.7.1**", "Windows GUI **1.4.1** · dump engine **2.7.2**")
        text = text.replace("Windows GUI 1.4.0", "Windows GUI 1.4.1")
        text = text.replace("dump engine 2.7.1", "dump engine 2.7.2")
        text = text.replace("Diagnostic 2.7.1", "Diagnostic 2.7.2")
        path.write_text(text, encoding="utf-8")

    release = ROOT / "docs" / "releases" / "diagnostic-2.7.2.md"
    release.write_text(
        """# TSUN Local Diagnostic 2.7.2\n\n"
        "Diagnostic 2.7.2 extends the full read-only capture with passive inspection of "
        "the logger network and firmware-update web interfaces.\n\n"
        "## Read-only web-interface research\n\n"
        "Full diagnostic mode now GETs a bounded set of local pages including "
        "`wireless.html`, `wizard.html`, `remote.html`, `update.html` and "
        "`invupdate.html`. It records only passive interface metadata: form methods, "
        "same-device action paths, field names/types, local script paths and JavaScript "
        "handler names. It never submits a form, executes JavaScript, uploads firmware "
        "or reboots a logger.\n\n"
        "## Windows updater\n\n"
        "The Windows GUI is 1.4.1. The updater now also compares the embedded dump-engine "
        "version. A newer dump engine therefore refreshes the portable EXE even when the "
        "GUI version itself did not otherwise change.\n\n"
        "## Safety\n\n"
        "The diagnostic remains strictly local, privacy-safe and read-only. DNS addresses, "
        "full serial numbers, full MAC addresses and credentials are not stored.\n"
        """,
        encoding="utf-8",
    )

    # One-shot bootstrap files remove themselves from the resulting patch.
    for relative in (
        "tools/_apply_diag_272_patch.py",
        ".github/workflows/_apply-diag-272.yml",
    ):
        path = ROOT / relative
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
