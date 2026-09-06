from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Expected exactly one match in {path}: {old[:100]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    dump = ROOT / "tools" / "tsun_dump.py"
    tests = ROOT / "tests" / "test_tsun_dump_tool.py"

    replace_once(dump, 'TOOL_VERSION = "2.7.2"', 'TOOL_VERSION = "2.7.3"')

    replace_once(
        dump,
        'LOGGER_AT_MAX_RESPONSE = 2048\nLOGGER_STATUS_PATHS =',
        'LOGGER_AT_MAX_RESPONSE = 2048\n'
        'LOGGER_JS_RESEARCH_FUNCTIONS = (\n'
        '    "sta_form_apply",\n'
        '    "step_setting_apply",\n'
        '    "server_setting_apply",\n'
        '    "sw_upload_apply",\n'
        '    "yzsw_upload_apply",\n'
        '    "internetSet",\n'
        '    "wirelessSet",\n'
        ')\n'
        'MAX_JS_FUNCTION_BODY = 6000\n'
        'LOGGER_STATUS_PATHS =',
    )

    marker = '''class _WebInterfaceParser(HTMLParser):\n    """Summarize forms and event hooks without submitting or executing them."""\n'''
    insertion = r'''def _extract_js_function_body(document: str, name: str) -> str | None:
    """Return one JavaScript function body by static source inspection only."""
    escaped = re.escape(name)
    patterns = (
        re.compile(rf"\bfunction\s+{escaped}\s*\([^)]*\)\s*\{{", re.IGNORECASE),
        re.compile(rf"\b{escaped}\s*=\s*function\s*\([^)]*\)\s*\{{", re.IGNORECASE),
    )
    match = next((candidate.search(document) for candidate in patterns if candidate.search(document)), None)
    if match is None:
        return None

    start = match.end() - 1
    depth = 0
    quote: str | None = None
    escaped_char = False
    line_comment = False
    block_comment = False

    for index in range(start, min(len(document), start + 20000)):
        char = document[index]
        nxt = document[index + 1] if index + 1 < len(document) else ""

        if line_comment:
            if char in "\r\n":
                line_comment = False
            continue
        if block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
            continue
        if quote is not None:
            if escaped_char:
                escaped_char = False
            elif char == "\\":
                escaped_char = True
            elif char == quote:
                quote = None
            continue
        if char == "/" and nxt == "/":
            line_comment = True
            continue
        if char == "/" and nxt == "*":
            block_comment = True
            continue
        if char in ('"', "'", "`"):
            quote = char
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return document[start + 1:index]
    return None


def summarize_js_research_functions(document: str) -> list[dict[str, Any]]:
    """Capture privacy-scrubbed source bodies of selected logger JS functions."""
    result: list[dict[str, Any]] = []
    for name in LOGGER_JS_RESEARCH_FUNCTIONS:
        body = _extract_js_function_body(document, name)
        if body is None:
            continue
        scrubbed = anonymize_web_document(body).strip()
        truncated = len(scrubbed) > MAX_JS_FUNCTION_BODY
        if truncated:
            scrubbed = scrubbed[:MAX_JS_FUNCTION_BODY]
        result.append(
            {
                "name": name,
                "body": scrubbed,
                "body_sha256": hashlib.sha256(scrubbed.encode("utf-8")).hexdigest(),
                "truncated": truncated,
                "static_source_only": True,
                "javascript_executed": False,
            }
        )
    return result


'''
    text = dump.read_text(encoding="utf-8")
    if text.count(marker) != 1:
        raise RuntimeError("WebInterfaceParser marker not found exactly once")
    dump.write_text(text.replace(marker, insertion + marker, 1), encoding="utf-8")

    replace_once(
        dump,
        '    return {\n        "path": current_path,\n        "forms": forms,\n        "script_paths": script_paths,\n        "javascript_handlers": sorted(parser.handlers),',
        '    return {\n'
        '        "path": current_path,\n'
        '        "forms": forms,\n'
        '        "script_paths": script_paths,\n'
        '        "javascript_handlers": sorted(parser.handlers),\n'
        '        "javascript_function_sources": summarize_js_research_functions(document),',
    )

    replace_once(
        dump,
        '            if candidate.lower() in placeholders:\n                continue\n            return candidate',
        '            if candidate.lower() in placeholders or candidate.isdigit():\n'
        '                continue\n'
        '            return candidate',
    )

    replace_once(tests, 'self.assertEqual(TOOL.TOOL_VERSION, "2.7.2")', 'self.assertEqual(TOOL.TOOL_VERSION, "2.7.3")')
    replace_once(
        tests,
        '    def test_dns_probe_command_is_get_only(self) -> None:\n',
        '''    def test_logger_firmware_fallback_rejects_plain_numeric_ui_value(self) -> None:\n        self.assertIsNone(TOOL._extract_logger_firmware("Firmware version: 13"))\n        self.assertEqual(\n            TOOL._extract_logger_firmware('var cover_ver="LSW5_SSL_02B0_1.05"; Firmware version: 13'),\n            "LSW5_SSL_02B0_1.05",\n        )\n\n    def test_js_research_extracts_target_body_without_execution_or_secrets(self) -> None:\n        document = (\n            'function sta_form_apply(){'\n            'var dns=document.forms[0].wan_setting_dns.value;'\n            'var password="TopSecret";'\n            'document.forms[0].action="do_step_neth.html";'\n            'document.forms[0].submit();'\n            '}'\n            'function unrelated(){return 1;}'\n        )\n        summaries = TOOL.summarize_js_research_functions(document)\n        self.assertEqual(len(summaries), 1)\n        summary = summaries[0]\n        self.assertEqual(summary["name"], "sta_form_apply")\n        self.assertTrue(summary["static_source_only"])\n        self.assertFalse(summary["javascript_executed"])\n        self.assertIn("wan_setting_dns", summary["body"])\n        self.assertIn("do_step_neth.html", summary["body"])\n        self.assertNotIn("TopSecret", summary["body"])\n        self.assertNotIn("unrelated", repr(summaries))\n\n    def test_js_function_parser_handles_nested_blocks(self) -> None:\n        document = 'function sw_upload_apply(){if(true){while(false){x();}}return 1;}'\n        body = TOOL._extract_js_function_body(document, "sw_upload_apply")\n        self.assertIsNotNone(body)\n        self.assertIn("while(false){x();}", body)\n        self.assertIn("return 1", body)\n\n    def test_dns_probe_command_is_get_only(self) -> None:\n''',
    )

    for relative in ("README.md", "tools/README.md", "docs/HARDWARE_DUMP.md", "docs/test-your-inverter.html"):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        text = text.replace("dump engine **2.7.2**", "dump engine **2.7.3**")
        text = text.replace("dump engine 2.7.2", "dump engine 2.7.3")
        text = text.replace("Diagnostic 2.7.2", "Diagnostic 2.7.3")
        path.write_text(text, encoding="utf-8")

    release = ROOT / "docs" / "releases" / "diagnostic-2.7.3.md"
    release.write_text(
        "# TSUN Local Diagnostic 2.7.3\n\n"
        "Diagnostic 2.7.3 deepens the strictly read-only logger web research.\n\n"
        "## Static JavaScript research\n\n"
        "Full diagnostic mode now extracts privacy-scrubbed source bodies for selected logger functions related to network/DNS, remote-server configuration and firmware upload. The source is parsed as text only: JavaScript is never executed, forms are never submitted, and no POST, firmware upload, reboot or configuration write is performed.\n\n"
        "Targeted functions include `sta_form_apply`, `step_setting_apply`, `server_setting_apply`, `sw_upload_apply`, `yzsw_upload_apply`, `internetSet` and `wirelessSet`. Function bodies are bounded and include a SHA-256 for comparison across logger firmware versions.\n\n"
        "## Metadata fix\n\n"
        "The generic logger-firmware fallback now rejects plain numeric UI/help values such as `13`, while explicit `cover_ver` / `webdata_ver` firmware variables remain preferred.\n\n"
        "## Windows bundle\n\n"
        "The GUI remains 1.4.1. Its updater already refreshes the Windows bundle when the embedded dump engine is older, so publishing dump engine 2.7.3 is sufficient to update existing 1.4.1 executables.\n\n"
        "## Safety\n\n"
        "Local, privacy-safe and strictly read-only. No logger or inverter write operation is added.\n",
        encoding="utf-8",
    )

    for relative in ("tools/_apply_diag_273_patch.py", ".github/workflows/_apply-diag-273.yml"):
        path = ROOT / relative
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    main()
